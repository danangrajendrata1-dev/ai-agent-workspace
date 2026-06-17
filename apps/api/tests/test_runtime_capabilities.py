from types import SimpleNamespace
from unittest.mock import patch

from app.services.runtime_capability_service import list_runtime_capabilities

from .test_sessions import auth_headers


def test_runtime_capabilities_endpoint_returns_safe_metadata_only(client):
    user = SimpleNamespace(id="9f5b7a5b-9c2c-4c7d-bb8b-4f0b4e8dc111", role="user")

    with patch("app.services.auth_service.get_current_active_user", return_value=user):
        response = client.get("/runtime/capabilities", headers=auth_headers(user.id))

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"items"}
    assert payload["items"]

    for item in payload["items"]:
        assert set(item.keys()) == {
            "key",
            "status",
            "label",
            "description",
            "requires_confirmation",
            "user_visible",
        }
        assert "url" not in item["key"].lower()
        assert "secret" not in item["label"].lower()
        assert "credential" not in item["description"].lower()
        assert item["user_visible"] is True
        assert item["status"] in {"disabled", "suggestion_only", "explicit_confirm", "forbidden"}


def test_runtime_capability_matrix_marks_expected_states():
    matrix = {item.key: item for item in list_runtime_capabilities()}

    assert matrix["chat.workflow_suggestion"].status == "suggestion_only"
    assert matrix["chat.workflow_suggestion"].requires_confirmation is False

    assert matrix["workflow.explicit_execute"].status == "explicit_confirm"
    assert matrix["workflow.explicit_execute"].requires_confirmation is True

    assert matrix["workflow.chat_confirm_execute"].status == "explicit_confirm"
    assert matrix["workflow.chat_confirm_execute"].requires_confirmation is True

    assert matrix["tool.execution"].status == "forbidden"
    assert matrix["tool_skill.execution"].status == "forbidden"
    assert matrix["custom_webhook.execution"].status == "forbidden"
    assert matrix["user_supplied_webhook.execution"].status == "forbidden"
    assert matrix["oauth.connection"].status == "forbidden"
    assert matrix["payment.billing"].status == "forbidden"

    assert matrix["workflow.execution_history"].status == "disabled"
    assert matrix["workflow.execution_history"].requires_confirmation is False
    assert matrix["workflow.execution_history"].user_visible is True
