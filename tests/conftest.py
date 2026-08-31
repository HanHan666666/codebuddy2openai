"""Shared fixtures. Import converter.py once per session and isolate CONFIG between tests."""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def converter_module():
    """Import converter.py by path, once per session, without running main()."""
    spec = importlib.util.spec_from_file_location(
        "converter_under_test", REPO_ROOT / "converter.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["converter_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def fresh_config(converter_module):
    """Reset CONFIG to defaults so tests cannot leak state into each other."""
    converter_module.CONFIG["api_key"] = ""
    converter_module.CONFIG["desensitize"] = False
    converter_module.CONFIG["log_path"] = None
    converter_module.CONFIG["direct_key"] = None
    converter_module.CONFIG["cred"] = None
    yield converter_module.CONFIG
    converter_module.CONFIG["api_key"] = ""
    converter_module.CONFIG["desensitize"] = False
    converter_module.CONFIG["log_path"] = None
    converter_module.CONFIG["direct_key"] = None
    converter_module.CONFIG["cred"] = None


@pytest.fixture()
def client(converter_module, fresh_config):
    """FastAPI TestClient wired to a converter with no credentials."""
    from fastapi.testclient import TestClient

    return TestClient(converter_module.app)


@pytest.fixture()
def authed_client(converter_module, client):
    converter_module.CONFIG["api_key"] = "test-key"
    client.headers.update({"Authorization": "Bearer test-key"})
    return client


@pytest.fixture()
def direct_key_client(authed_client, converter_module):
    converter_module.CONFIG["direct_key"] = "ck_test_dummy"
    return authed_client


@pytest.fixture()
def fake_auth_file(tmp_path):
    """A plausible desktop auth file for the WorkBuddy international realm."""
    auth_dir = tmp_path / "CodeBuddyExtension" / "Data" / "Public" / "auth"
    auth_dir.mkdir(parents=True)
    payload = {
        "account": {
            "uid": "test-uid-1234",
            "nickname": "tester@example.com",
            "enterpriseId": None,
        },
        "auth": {
            "accessToken": "test-access-token",
            "refreshToken": "test-refresh-token",
            "expiresAt": 9999999999999,
            "domain": "www.workbuddy.ai",
        },
    }
    auth_file = auth_dir / "workbuddy-desktop-ai.info"
    auth_file.write_text(__import__("json").dumps(payload), encoding="utf-8")
    return auth_file, payload
