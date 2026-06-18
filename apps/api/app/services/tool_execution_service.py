import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import (
    agent_repository,
    agent_tool_repository,
    approval_repository,
    task_repository,
    tool_repository,
)
from app.schemas.tool_execution import ToolExecutionRequest, ToolExecutionResponse
from app.services import log_service


GLOBAL_TOOL_EXECUTION_BLOCK_REASON = "Tool execution is disabled in this release."


def validate_tool_permission(
    db: Session,
    *,
    owner_id: uuid.UUID,
    payload: ToolExecutionRequest,
) -> dict:
    agent = agent_repository.get_by_id(db, owner_id, payload.agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    task = task_repository.get_by_id(db, owner_id, payload.task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    if task.agent_id != agent.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task and agent must match.",
        )

    tool = tool_repository.get_by_id(db, payload.tool_id)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        )

    assignment = agent_tool_repository.get_assignment(db, agent.id, tool.id)
    if assignment is None:
        return {
            "agent": agent,
            "task": task,
            "tool": tool,
            "assignment": None,
            "blocked_reason": "Tool is not assigned to this agent.",
        }

    if assignment.permission_mode == "block":
        return {
            "agent": agent,
            "task": task,
            "tool": tool,
            "assignment": assignment,
            "blocked_reason": "Tool is explicitly blocked for this agent.",
        }

    if not assignment.is_enabled:
        return {
            "agent": agent,
            "task": task,
            "tool": tool,
            "assignment": assignment,
            "blocked_reason": "Tool assignment is disabled for this agent.",
        }

    if tool.status != "active":
        return {
            "agent": agent,
            "task": task,
            "tool": tool,
            "assignment": assignment,
            "blocked_reason": "Tool must be active to be requested.",
        }

    if tool.risk_level == "critical":
        return {
            "agent": agent,
            "task": task,
            "tool": tool,
            "assignment": assignment,
            "blocked_reason": "Critical tool execution is disabled in MVP.",
        }

    if tool.tool_type == "github" or tool.source_type == "github":
        return {
            "agent": agent,
            "task": task,
            "tool": tool,
            "assignment": assignment,
            "blocked_reason": "GitHub imported tool execution is disabled in MVP.",
        }

    return {
        "agent": agent,
        "task": task,
        "tool": tool,
        "assignment": assignment,
        "blocked_reason": None,
    }


def should_require_approval(*, agent, tool, assignment) -> bool:
    if assignment.override_approval_required is True:
        return True
    if agent.requires_approval_by_default:
        return True
    if tool.approval_required:
        return True
    if tool.risk_level in {"high", "critical"}:
        return True
    return False


def create_waiting_approval_request(
    db: Session,
    *,
    task,
    agent,
    tool,
    masked_input_payload: dict | None,
):
    approval_request = approval_repository.create(
        db,
        {
            "task_id": task.id,
            "agent_id": agent.id,
            "tool_id": tool.id,
            "requested_action": f"Approve tool request for {tool.name}.",
            "risk_level": tool.risk_level,
            "status": "pending",
            "request_payload": masked_input_payload,
            "decision_reason": None,
            "decided_by": None,
            "decided_at": None,
        },
    )
    task_repository.update_status(db, task, "waiting_approval")
    return approval_request


def record_tool_call_stub(
    db: Session,
    *,
    task_id: uuid.UUID,
    tool_id: uuid.UUID,
    agent_id: uuid.UUID,
    input_payload: dict | None,
    output_payload: dict | None,
    status_value: str,
    error_message: str | None = None,
):
    return log_service.record_tool_call(
        db,
        task_id=task_id,
        tool_id=tool_id,
        agent_id=agent_id,
        input_payload=input_payload,
        output_payload=output_payload,
        status=status_value,
        latency_ms=0,
        error_message=error_message,
    )


def request_tool_execution_stub(
    db: Session,
    *,
    owner_id: uuid.UUID,
    payload: ToolExecutionRequest,
) -> ToolExecutionResponse:
    permission_result = validate_tool_permission(db, owner_id=owner_id, payload=payload)
    agent = permission_result["agent"]
    task = permission_result["task"]
    tool = permission_result["tool"]
    blocked_reason = permission_result["blocked_reason"] or GLOBAL_TOOL_EXECUTION_BLOCK_REASON

    masked_input_payload = log_service.mask_sensitive_data(payload.input_payload)

    tool_call = record_tool_call_stub(
        db,
        task_id=task.id,
        tool_id=tool.id,
        agent_id=agent.id,
        input_payload=masked_input_payload,
        output_payload={"stub": True, "message": blocked_reason},
        status_value="blocked",
        error_message=blocked_reason,
    )
    log_service.record_activity(
        db,
        actor_type="agent",
        actor_id=agent.id,
        request_id=task.request_id,
        event_type="tool.execution.stubbed",
        message="Tool execution request was blocked safely.",
        metadata_json={
            "tool_id": str(tool.id),
            "risk_level": tool.risk_level,
            "reason": blocked_reason,
        },
    )
    db.commit()
    db.refresh(tool_call)
    return ToolExecutionResponse(
        status="blocked",
        message="Tool execution is disabled in this release.",
        approval_required=False,
        approval_request_id=None,
        tool_call_id=tool_call.id,
        execution_performed=False,
        risk_level=tool.risk_level,
        blocked_reason=blocked_reason,
    )
