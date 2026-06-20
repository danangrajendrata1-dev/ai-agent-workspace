import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from app.services.approval_service import serialize_approval
from app.services.log_service import serialize_model_usage_log, serialize_tool_call
from app.services.task_service import serialize_task_detail


def _now():
    return datetime.now(UTC)


def test_log_serializers_redact_nested_secrets_and_error_messages():
    tool_call = SimpleNamespace(
        id=uuid.uuid4(),
        task_id=uuid.uuid4(),
        tool_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        input_payload={
            "token": "sk-live-12345678",
            "nested": [{"password": "super-secret"}],
            "note": "Bearer abcdef",
        },
        output_payload={
            "result": "ok",
            "api_key": "secret-value",
        },
        status="failed",
        latency_ms=25,
        error_message="token leaked in error",
        created_at=_now(),
    )
    model_usage = SimpleNamespace(
        id=uuid.uuid4(),
        provider_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        task_id=uuid.uuid4(),
        model_name="gpt-4o-mini",
        prompt_tokens=10,
        completion_tokens=5,
        estimated_cost=None,
        latency_ms=99,
        status="failed",
        error_message="password leaked in response",
        created_at=_now(),
    )

    tool_result = serialize_tool_call(tool_call)
    model_usage_result = serialize_model_usage_log(model_usage)

    assert tool_result.input_payload["token"] == "***"
    assert tool_result.input_payload["nested"][0]["password"] == "***"
    assert tool_result.input_payload["note"] == "Sensitive content redacted."
    assert tool_result.output_payload["api_key"] == "***"
    assert tool_result.error_message == "Sensitive content redacted."
    assert model_usage_result.error_message == "Sensitive content redacted."


def test_task_serializer_redacts_sensitive_text_in_task_detail():
    task = SimpleNamespace(
        id=uuid.uuid4(),
        request_id="request-123",
        owner_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        input_text="Use token sk-live-12345678 for this task.",
        status="failed",
        selected_skill_id=None,
        selected_tool_id=None,
        final_response="Password secret-value should not be returned.",
        error_message="Authorization bearer token leaked.",
        started_at=_now(),
        completed_at=_now(),
        created_at=_now(),
        updated_at=_now(),
    )
    step = SimpleNamespace(
        id=uuid.uuid4(),
        task_id=task.id,
        step_order=1,
        step_name="completed",
        status="failed",
        input_summary="token sk-live-12345678",
        output_summary="password secret-value",
        error_message="bearer token leaked",
        created_at=_now(),
    )

    result = serialize_task_detail(task, [step])

    assert result.input_text == "Sensitive content redacted."
    assert result.final_response == "Sensitive content redacted."
    assert result.error_message == "Sensitive content redacted."
    assert result.steps[0].input_summary == "Sensitive content redacted."
    assert result.steps[0].output_summary == "Sensitive content redacted."
    assert result.steps[0].error_message == "Sensitive content redacted."


def test_approval_serializer_redacts_nested_request_payload():
    approval = SimpleNamespace(
        id=uuid.uuid4(),
        task_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        tool_id=uuid.uuid4(),
        requested_action="Run tool safely",
        risk_level="high",
        status="pending",
        request_payload={
            "outer": {
                "api_key": "sk-live-12345678",
                "items": [{"secret": "nested-secret"}],
            },
            "reason": "Bearer abcdef",
        },
        decision_reason="token leaked in review note",
        decided_by=None,
        decided_at=None,
        created_at=_now(),
    )

    result = serialize_approval(approval)

    assert result.request_payload["outer"]["api_key"] == "***"
    assert result.request_payload["outer"]["items"][0]["secret"] == "***"
    assert result.request_payload["reason"] == "Sensitive content redacted."
    assert result.decision_reason == "Sensitive content redacted."
