import os
from pathlib import Path

from fastapi.testclient import TestClient

from api import app as app_module


def test_api_is_get_only_and_serves_fictional_state(
    demo_root: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SDOC_DATA_ROOT", str(demo_root))
    app_module._state.cache_clear()
    with TestClient(app_module.app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["read_only"] is True
        overview = client.get("/api/overview")
        assert overview.status_code == 200
        assert overview.json()["dataset"]["label"] == "fictional demo"
        emails = client.get("/api/emails?subset=mismatches")
        assert emails.status_code == 200
        assert emails.json()["count"] == 1
        story = client.get("/api/emails/email_001/story")
        assert story.status_code == 200
        assert story.json()["verdict"]["status"] == "OK"

    methods = {
        method
        for route in app_module.app.routes
        for method in getattr(route, "methods", set())
    }
    assert methods <= {"GET", "HEAD", "OPTIONS"}


def test_api_does_not_create_runtime_directories(
    demo_root: Path, monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("SDOC_DATA_ROOT", str(demo_root))
    app_module._state.cache_clear()
    before = set(tmp_path.iterdir())
    with TestClient(app_module.app) as client:
        client.get("/api/overview")
    assert set(tmp_path.iterdir()) == before
    assert not (demo_root / ".demo-logs").exists()


def test_unknown_story_is_not_found(demo_root: Path, monkeypatch) -> None:
    monkeypatch.setenv("SDOC_DATA_ROOT", str(demo_root))
    app_module._state.cache_clear()
    with TestClient(app_module.app) as client:
        response = client.get("/api/emails/not-present/story")
    assert response.status_code == 404


def test_environment_is_not_loaded_implicitly(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEYS", raising=False)
    from sdoc_verifier.llm import load_api_keys_from_env

    assert load_api_keys_from_env() == []
    assert "GEMINI_API_KEYS" not in os.environ or not os.environ["GEMINI_API_KEYS"]
