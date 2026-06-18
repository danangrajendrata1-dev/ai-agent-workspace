from types import SimpleNamespace
from unittest.mock import patch

from .test_sessions import auth_headers


def test_runtime_readiness_endpoint_returns_safe_metadata_only(client):
    user = SimpleNamespace(id="9f5b7a5b-9c2c-4c7d-bb8b-4f0b4e8dc111", role="user")

    with patch("app.services.auth_service.get_current_active_user", return_value=user):
        response = client.get("/runtime/readiness", headers=auth_headers(user.id))

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "status",
        "message",
        "runtime_execution_enabled",
        "tool_execution_enabled",
        "model_raw_generation_enabled",
        "requires_future_safety_review",
        "docs_path",
    }
    assert payload["status"] == "disabled"
    assert payload["runtime_execution_enabled"] is False
    assert payload["tool_execution_enabled"] is False
    assert payload["model_raw_generation_enabled"] is False
    assert payload["requires_future_safety_review"] is True
    assert payload["docs_path"] == "docs/agent-runtime-readiness.md"
    assert "execution_available" not in payload
    assert "secret" not in payload["message"].lower()
    assert "http://" not in payload["docs_path"].lower()
    assert "https://" not in payload["docs_path"].lower()
    assert "url" not in payload["message"].lower()
