"""Unit tests for pure helpers added or touched by the API key mode."""

import json
import time

import pytest


class TestBackendForDomain:
    def test_workbuddy_domain_maps_to_international_backend(self, converter_module):
        assert (
            converter_module.backend_for_domain("www.workbuddy.ai")
            == "https://www.workbuddy.ai"
        )

    def test_china_domain_maps_to_copilot_backend(self, converter_module):
        assert (
            converter_module.backend_for_domain("www.codebuddy.cn")
            == "https://copilot.tencent.com"
        )

    def test_none_domain_falls_back_to_china_backend(self, converter_module):
        assert (
            converter_module.backend_for_domain(None)
            == "https://copilot.tencent.com"
        )

    def test_unknown_domain_falls_back_to_china_backend(self, converter_module):
        assert (
            converter_module.backend_for_domain("example.invalid")
            == "https://copilot.tencent.com"
        )


class TestModelCatalogs:
    def test_china_catalog_matches_upstream_defaults(self, converter_module):
        # The desktop-token path must serve the same list as upstream.
        expected = [
            "glm-5.2", "glm-5.1", "glm-5v-turbo",
            "kimi-k2.7", "kimi-k2.6", "kimi-k2.5",
            "deepseek-v4-pro", "deepseek-v4-flash",
            "minimax-m3-pay", "hy3-preview-agent", "auto",
        ]
        assert converter_module.DEFAULT_MODELS == expected
        assert converter_module.CN_MODELS == expected

    def test_international_catalog_is_separate_list(self, converter_module):
        assert converter_module.INTL_MODELS is not converter_module.CN_MODELS
        assert converter_module.INTL_MODELS != converter_module.CN_MODELS

    def test_international_catalog_contains_gpt56_family(self, converter_module):
        for model in ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"):
            assert model in converter_module.INTL_MODELS

    def test_international_catalog_contains_hy3_lowercase(self, converter_module):
        # Upstream rejects "Hy3"; the catalog must advertise the working id.
        assert "hy3" in converter_module.INTL_MODELS
        assert "Hy3" not in converter_module.INTL_MODELS

    def test_auto_present_in_both_catalogs(self, converter_module):
        assert "auto" in converter_module.CN_MODELS
        assert "auto" in converter_module.INTL_MODELS

    def test_no_duplicate_ids_within_a_catalog(self, converter_module):
        assert len(converter_module.CN_MODELS) == len(set(converter_module.CN_MODELS))
        assert len(converter_module.INTL_MODELS) == len(set(converter_module.INTL_MODELS))


class TestFindAuthFile:
    def test_finds_info_file_in_windows_layout(self, converter_module, tmp_path, monkeypatch):
        auth_dir = tmp_path / "CodeBuddyExtension" / "Data" / "Public" / "auth"
        auth_dir.mkdir(parents=True)
        (auth_dir / "workbuddy-desktop-ai.info").write_text("{}", encoding="utf-8")
        monkeypatch.setattr(converter_module, "auth_dirs", lambda: [auth_dir])
        found = converter_module.find_auth_file()
        assert found is not None and found.name == "workbuddy-desktop-ai.info"

    def test_returns_none_when_directory_missing(self, converter_module, tmp_path, monkeypatch):
        monkeypatch.setattr(converter_module, "auth_dirs", lambda: [tmp_path / "missing"])
        assert converter_module.find_auth_file() is None


class TestCredentialManager:
    def _manager(self, converter_module, path):
        return converter_module.CredentialManager(path)

    def test_loads_session_from_auth_file(self, converter_module, fake_auth_file):
        path, payload = fake_auth_file
        manager = self._manager(converter_module, path)
        assert manager._session() == payload

    def test_not_expired_for_far_future_token(self, converter_module, fake_auth_file):
        path, _ = fake_auth_file
        manager = self._manager(converter_module, path)
        assert manager._is_expired() is False

    def test_expired_for_past_token(self, converter_module, tmp_path):
        path = tmp_path / "expired.info"
        payload = {
            "account": {"uid": "u", "nickname": "n"},
            "auth": {"accessToken": "t", "expiresAt": int(time.time() * 1000) - 10_000},
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        manager = self._manager(converter_module, path)
        assert manager._is_expired() is True

    def test_missing_file_raises_on_session_access(self, converter_module, tmp_path):
        manager = self._manager(converter_module, tmp_path / "absent.info")
        with pytest.raises(RuntimeError, match="auth"):
            manager._session()

    def test_headers_carry_bearer_and_user_id(self, converter_module, fake_auth_file):
        path, payload = fake_auth_file
        manager = self._manager(converter_module, path)
        headers = manager.get_headers()
        assert headers["Authorization"] == "Bearer test-access-token"
        assert headers["X-User-Id"] == "test-uid-1234"
        assert headers["X-Domain"] == "www.workbuddy.ai"

    def test_summary_exposes_nickname(self, converter_module, fake_auth_file):
        path, _ = fake_auth_file
        manager = self._manager(converter_module, path)
        summary = manager.summary()
        assert summary.get("nickname") == "tester@example.com"


class TestCheckAuth:
    def test_open_access_when_no_server_key_configured(self, converter_module, fresh_config):
        # Without --api-key the converter does not require client credentials.
        converter_module._check_auth(None, None)

    def test_rejects_wrong_key(self, converter_module, fresh_config):
        from fastapi import HTTPException

        fresh_config["api_key"] = "expected"
        with pytest.raises(HTTPException) as exc:
            converter_module._check_auth("Bearer wrong", None)
        assert exc.value.status_code == 401

    def test_rejects_missing_header_when_server_key_set(self, converter_module, fresh_config):
        from fastapi import HTTPException

        fresh_config["api_key"] = "expected"
        with pytest.raises(HTTPException) as exc:
            converter_module._check_auth(None, None)
        assert exc.value.status_code == 401

    def test_accepts_matching_bearer_key(self, converter_module, fresh_config):
        fresh_config["api_key"] = "expected"
        converter_module._check_auth("Bearer expected", None)

    def test_accepts_matching_x_api_key_header(self, converter_module, fresh_config):
        fresh_config["api_key"] = "expected"
        converter_module._check_auth(None, "expected")

    def test_bearer_prefix_required_for_authorization_header(self, converter_module, fresh_config):
        from fastapi import HTTPException

        fresh_config["api_key"] = "expected"
        with pytest.raises(HTTPException):
            converter_module._check_auth("expected", None)


class TestCredGuard:
    def test_cred_raises_in_direct_key_mode(self, converter_module, fresh_config):
        from fastapi import HTTPException

        fresh_config["direct_key"] = "ck_something"
        with pytest.raises(HTTPException) as exc:
            converter_module._cred()
        assert exc.value.status_code == 500

    def test_cred_raises_without_credentials_outside_direct_mode(self, converter_module, fresh_config):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            converter_module._cred()
        assert exc.value.status_code == 503
