from types import SimpleNamespace
from unittest.mock import patch

from .test_sessions import auth_headers


def test_runtime_event_contract_endpoint_returns_safe_metadata_only(client):
    user = SimpleNamespace(id="9f5b7a5b-9c2c-4c7d-bb8b-4f0b4e8dc111", role="user")

    with patch("app.services.auth_service.get_current_active_user", return_value=user):
        response = client.get("/runtime/event-contract", headers=auth_headers(user.id))

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "status",
        "message",
        "event_status_values",
        "event_type_values",
        "confirmation_state_values",
        "event_fields",
        "forbidden_fields",
        "guard_requirements",
        "logging_rules",
        "runtime_event_table_enabled",
        "runtime_event_history_enabled",
        "docs_path",
    }
    assert payload["status"] == "disabled"
    assert payload["runtime_event_table_enabled"] is False
    assert payload["runtime_event_history_enabled"] is False
    assert payload["docs_path"] == "docs/agent-runtime-readiness.md"
    assert payload["event_status_values"] == [
        "disabled",
        "planned",
        "blocked",
        "queued_future",
        "running_future",
        "completed_future",
        "failed_future",
    ]
    assert payload["event_type_values"] == [
        "runtime_status",
        "guard_blocked",
        "future_execution_requested",
        "future_execution_completed",
        "future_execution_failed",
    ]
    assert payload["confirmation_state_values"] == [
        "not_required",
        "required",
        "confirmed_future",
        "denied",
    ]

    assert payload["forbidden_fields"] == [
        "raw_prompt",
        "raw_chat_message",
        "raw_knowledge_content",
        "raw_provider_response",
        "raw_tool_output",
        "raw_webhook_response",
        "provider_api_key",
        "credential",
        "token",
        "secret",
        "webhook_url",
        "request_headers",
        "response_headers",
        "arbitrary_url",
        "stack_trace",
    ]

    event_field_names = [field["name"] for field in payload["event_fields"]]
    assert event_field_names == [
        "event_id",
        "agent_id",
        "session_id",
        "status",
        "event_type",
        "capability_key",
        "safe_message",
        "created_at",
        "finished_at",
        "requires_confirmation",
        "confirmation_state",
        "safe_error_code",
        "safe_error_message",
    ]

    forbidden_tokens = [
        "http://",
        "https://",
        "internal url",
        "password=",
        "api key=",
        "database url=",
    ]
    payload_text = str(payload).lower()
    for token in forbidden_tokens:
        assert token not in payload_text


def test_runtime_event_contract_service_uses_safe_status_and_field_lists():
    from app.services.runtime_event_contract_service import get_runtime_event_contract

    contract = get_runtime_event_contract()

    assert contract.status == "disabled"
    assert contract.runtime_event_table_enabled is False
    assert contract.runtime_event_history_enabled is False
    assert "runtime" in contract.message.lower()
    assert "execution" in contract.message.lower()
