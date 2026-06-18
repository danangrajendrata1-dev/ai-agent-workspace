import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.schemas.model_router import ModelRouterRequest
from app.schemas.tool_execution import ToolExecutionRequest
from app.services.model_router_service import run_model_stub
from app.services.tool_execution_service import request_tool_execution_stub


def test_tool_execution_stub_is_blocked_and_never_marks_success():
    db = MagicMock()
    owner_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    task_id = uuid.uuid4()
    tool_id = uuid.uuid4()
    agent = SimpleNamespace(id=agent_id)
    task = SimpleNamespace(id=task_id, request_id="request-123")
    tool = SimpleNamespace(id=tool_id, risk_level="low")
    payload = ToolExecutionRequest(
        task_id=task_id,
        agent_id=agent_id,
        tool_id=tool_id,
        input_payload={"secret": "sk-live-12345678", "value": "keep"},
    )

    with patch(
        "app.services.tool_execution_service.validate_tool_permission",
        return_value={
            "agent": agent,
            "task": task,
            "tool": tool,
            "assignment": None,
            "blocked_reason": None,
        },
    ), patch(
        "app.services.tool_execution_service.log_service.record_tool_call",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ) as mock_record_tool_call, patch(
        "app.services.tool_execution_service.log_service.record_activity",
        return_value=None,
    ) as mock_record_activity:
        result = request_tool_execution_stub(db, owner_id=owner_id, payload=payload)

    assert result.status == "blocked"
    assert result.execution_performed is False
    assert result.approval_required is False
    assert result.approval_request_id is None
    assert result.blocked_reason == "Tool execution is disabled in this release."
    assert db.commit.called
    assert db.refresh.called
    assert mock_record_tool_call.call_args.kwargs["status"] == "blocked"
    assert mock_record_tool_call.call_args.kwargs["error_message"] == "Tool execution is disabled in this release."
    assert mock_record_activity.call_args.kwargs["event_type"] == "tool.execution.stubbed"
    assert "success" not in result.model_dump_json().lower()


def test_model_router_stub_is_blocked_and_records_no_success():
    db = MagicMock()
    owner_id = uuid.uuid4()
    provider_id = uuid.uuid4()
    provider = SimpleNamespace(
        id=provider_id,
        provider_type="api",
        default_model="gpt-4o-mini",
        status="active",
        is_private=True,
    )
    payload = ModelRouterRequest(
        provider_id=provider_id,
        prompt="Summarize this note",
    )

    with patch(
        "app.services.model_router_service.model_provider_repository.get_by_id",
        return_value=provider,
    ), patch(
        "app.services.model_router_service.log_service.record_model_usage",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ) as mock_record_model_usage:
        result = run_model_stub(db, owner_id=owner_id, payload=payload)

    assert result.provider_id == provider_id
    assert result.provider_type == "api"
    assert result.model_name == "gpt-4o-mini"
    assert result.stub is True
    assert "No model generation was performed." in result.output_text
    assert db.commit.called
    assert mock_record_model_usage.call_args.kwargs["status"] == "blocked"
    assert mock_record_model_usage.call_args.kwargs["error_message"] == "Model generation is disabled in this release."
    assert mock_record_model_usage.call_args.kwargs["prompt_tokens"] == 0
    assert mock_record_model_usage.call_args.kwargs["completion_tokens"] == 0
    assert "success" not in result.model_dump_json().lower()

