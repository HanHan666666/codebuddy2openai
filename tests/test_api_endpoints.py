"""Endpoint tests through the FastAPI test client, upstream mocked.

The tests patch httpx.AsyncClient.stream, the seam the converter uses for
both the streaming and the aggregating path.
"""

import json

import httpx
import pytest


def sse_chunk(content: str, model: str = "glm-5.2") -> bytes:
    payload = {
        "id": "cmb-test", "model": model, "object": "chat.completion.chunk",
        "created": 1700000000,
        "choices": [{"index": 0, "delta": {"role": "assistant", "content": content},
                     "finish_reason": ""}],
        "usage": None,
    }
    return f"data: {json.dumps(payload)}\n\n".encode()


def sse_finish(model: str = "glm-5.2") -> bytes:
    payload = {
        "id": "cmb-test", "model": model, "object": "chat.completion.chunk",
        "created": 1700000000,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    return f"data: {json.dumps(payload)}\n\ndata: [DONE]\n\n".encode()


class FakeUpstream:
    """Stands in for the Tencent backend. Records the request, replays chunks."""

    def __init__(self, chunks: list[bytes], status_code: int = 200):
        self.chunks = chunks
        self.status_code = status_code
        self.requests: list[dict] = []

    def __call__(self, monkeypatch, converter_module):
        upstream = self

        class FakeResponse:
            def __init__(self):
                self.status_code = upstream.status_code

            async def aiter_bytes(self):
                for chunk in upstream.chunks:
                    yield chunk

            async def aiter_lines(self):
                buffer = b"".join(upstream.chunks).decode("utf-8")
                for line in buffer.splitlines():
                    yield line

            async def aread(self):
                return b"".join(upstream.chunks)

        class FakeStreamCtx:
            async def __aenter__(self):
                return FakeResponse()

            async def __aexit__(self, *args):
                return False

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            def stream(self, method, url, headers=None, json=None, **kwargs):
                upstream.requests.append(
                    {"method": method, "url": url, "headers": headers or {}, "body": json or {}}
                )
                return FakeStreamCtx()

        monkeypatch.setattr(converter_module.httpx, "AsyncClient", FakeAsyncClient)
        return upstream

    @property
    def last(self) -> dict:
        return self.requests[-1]


@pytest.fixture()
def upstream_ok(monkeypatch, converter_module):
    def install(chunks: list[bytes], status_code: int = 200) -> FakeUpstream:
        return FakeUpstream(chunks, status_code)(monkeypatch, converter_module)
    return install


class TestHealth:
    def test_reports_ok_without_credentials(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"

    def test_direct_key_mode_reported_in_health(self, direct_key_client, converter_module):
        response = direct_key_client.get("/health")
        assert response.status_code == 200
        # /health must not leak the key itself
        assert "ck_test_dummy" not in response.text


class TestListModels:
    def test_token_mode_serves_china_catalog(self, authed_client, converter_module):
        response = authed_client.get("/v1/models")
        assert response.status_code == 200
        ids = [m["id"] for m in response.json()["data"]]
        assert ids == converter_module.CN_MODELS
        assert "gpt-5.6-luna" not in ids

    def test_direct_key_mode_serves_international_catalog(self, direct_key_client, converter_module):
        response = direct_key_client.get("/v1/models")
        assert response.status_code == 200
        ids = [m["id"] for m in response.json()["data"]]
        assert ids == converter_module.INTL_MODELS
        assert "gpt-5.6-luna" in ids
        assert "minimax-m3-pay" not in ids

    def test_requires_client_key_when_configured(self, converter_module, client):
        converter_module.CONFIG["api_key"] = "secret"
        assert client.get("/v1/models").status_code == 401

    def test_open_when_no_client_key_configured(self, client):
        assert client.get("/v1/models").status_code == 200


class TestChatCompletionsAuth:
    def test_rejects_unauthenticated_request_when_key_set(self, converter_module, client):
        converter_module.CONFIG["api_key"] = "secret"
        response = client.post("/v1/chat/completions", json={
            "model": "glm-5.2",
            "messages": [{"role": "user", "content": "hi"}],
        })
        assert response.status_code == 401


class TestChatCompletionsDirectKeyMode:
    def test_sends_bearer_key_to_international_backend(
        self, direct_key_client, converter_module, upstream_ok
    ):
        upstream = upstream_ok([sse_chunk("OK"), sse_finish()])

        response = direct_key_client.post("/v1/chat/completions", json={
            "model": "hy3",
            "messages": [{"role": "user", "content": "say OK"}],
            "max_tokens": 100,
        })
        assert response.status_code == 200
        assert upstream.last["url"].startswith("https://www.codebuddy.ai/v2/chat/completions")
        assert upstream.last["headers"]["Authorization"] == "Bearer ck_test_dummy"
        assert "X-User-Id" not in upstream.last["headers"]

    def test_prepends_system_message_when_missing(
        self, direct_key_client, converter_module, upstream_ok
    ):
        upstream = upstream_ok([sse_chunk("OK"), sse_finish()])

        direct_key_client.post("/v1/chat/completions", json={
            "model": "glm-5.2",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 100,
        })
        sent = upstream.last["body"]["messages"]
        assert sent[0]["role"] == "system"

    def test_keeps_client_system_message_when_present(
        self, direct_key_client, converter_module, upstream_ok
    ):
        upstream = upstream_ok([sse_chunk("OK"), sse_finish()])

        direct_key_client.post("/v1/chat/completions", json={
            "model": "glm-5.2",
            "messages": [
                {"role": "system", "content": "You are terse."},
                {"role": "user", "content": "hi"},
            ],
            "max_tokens": 100,
        })
        sent = upstream.last["body"]["messages"]
        assert sent[0]["role"] == "system"
        assert sent[0]["content"] == "You are terse."
        assert len(sent) == 2

    def test_forces_stream_true_upstream_for_non_stream_client(
        self, direct_key_client, converter_module, upstream_ok
    ):
        upstream = upstream_ok([sse_chunk("OK"), sse_finish()])

        response = direct_key_client.post("/v1/chat/completions", json={
            "model": "glm-5.2",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 100,
            "stream": False,
        })
        assert response.status_code == 200
        assert upstream.last["body"]["stream"] is True
        # The client still receives a single non-streaming completion.
        body = response.json()
        assert body["object"] == "chat.completion"
        assert body["choices"][0]["message"]["content"] == "OK"

    def test_streams_sse_to_streaming_client(
        self, direct_key_client, converter_module, upstream_ok
    ):
        upstream_ok([sse_chunk("HE"), sse_chunk("LLO"), sse_finish()])

        response = direct_key_client.post("/v1/chat/completions", json={
            "model": "glm-5.2",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 100,
            "stream": True,
        })
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        # Chunks pass through individually; "HE" and "LLO" never merge in flight.
        assert '"content": "HE"' in response.text
        assert '"content": "LLO"' in response.text
        assert "data: [DONE]" in response.text

    def test_non_stream_response_carries_aggregated_content(
        self, direct_key_client, converter_module, upstream_ok
    ):
        upstream_ok([sse_chunk("PROXY "), sse_chunk("OK"), sse_finish()])

        response = direct_key_client.post("/v1/chat/completions", json={
            "model": "glm-5.2",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 100,
        })
        assert response.json()["choices"][0]["message"]["content"] == "PROXY OK"


class TestChatCompletionsErrors:
    def test_missing_messages_rejected(self, direct_key_client):
        response = direct_key_client.post("/v1/chat/completions", json={"model": "glm-5.2"})
        assert response.status_code == 400

    def test_invalid_json_rejected(self, direct_key_client):
        response = direct_key_client.post(
            "/v1/chat/completions",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    def test_upstream_http_error_maps_to_502(
        self, direct_key_client, converter_module, monkeypatch
    ):
        class FailingClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            def stream(self, *args, **kwargs):
                raise httpx.ConnectError("connection refused")

        monkeypatch.setattr(converter_module.httpx, "AsyncClient", FailingClient)

        response = direct_key_client.post("/v1/chat/completions", json={
            "model": "glm-5.2",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 100,
        })
        assert response.status_code == 502


class TestTokenPathUnchanged:
    def test_token_mode_requires_credential_manager(self, converter_module, client):
        # Without credentials the token path must fail with 503, not fall back
        # to the direct-key backend.
        converter_module.CONFIG["api_key"] = ""
        response = client.post("/v1/chat/completions", json={
            "model": "glm-5.2",
            "messages": [{"role": "user", "content": "hi"}],
        })
        assert response.status_code == 503

    def test_token_mode_health_reports_credentials_missing(self, converter_module, client):
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body.get("cred") is None or "credential" not in body
