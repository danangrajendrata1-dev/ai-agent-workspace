import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import agent_repository, approval_repository, task_repository, tool_repository
from app.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalRequestCreate,
    ApprovalRequestResponse,
)
from app.services import log_service


SECRET_KEY_PATTERNS = [
    r"(?i)\bAPI_KEY\b",
    r"(?i)\bDATABASE_URL\b",
    r"(?i)\bpassword\b",
    r"(?i)\bbearer\b",
    r"(?i)\bsk-[A-Za-z0-9_\-]+\b",
]


def mask_request_payload(payload):
    if payload is None:
        return None

    masked = {}
    for key, value in payload.items():
        key_text = str(key)
        if any(re.search(pattern, key_text) for pattern in SECRET_KEY_PATTERNS):
            masked[key] = "***"
            continue

        if isinstance(value, str) and any(re.search(pattern, value) for pattern in SECRET_KEY_PATTERNS):
            masked[key] = "***"
        else:
            masked[key] = value
    return masked


def serialize_approval(approval_request) -> ApprovalRequestResponse:
    return ApprovalRequestResponse(
        id=approval_request.id,
        task_id=approval_request.task_id,
        agent_id=approval_request.agent_id,
        tool_id=approval_request.tool_id,
        requested_action=approval_request.requested_action,
        risk_level=approval_request.risk_level,
        status=approval_request.status,
        request_payload=mask_request_payload(approval_request.request_payload),
        decision_reason=approval_request.decision_reason,
        decided_by=approval_request.decided_by,
        decided_at=approval_request.decided_at,
        created_at=approval_request.created_at,
    )


def validate_owner_access(db: Session, *, owner_id: uuid.UUID, approval_request) -> None:
    task = task_repository.get_by_id(db, owner_id, approval_request.task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found.",
        )


def create_approval_request(
    db: Session,
    *,
    owner_id: uuid.UUID,
    payload: ApprovalRequestCreate,
) -> ApprovalRequestResponse:
    task = task_repository.get_by_id(db, owner_id, payload.task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task must belong to the current owner.",
        )

    agent = agent_repository.get_by_id(db, owner_id, payload.agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent must belong to the current owner.",
        )

    if task.agent_id != agent.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task and agent must match for approval creation.",
        )

    if payload.tool_id is not None:
        tool = tool_repository.get_by_id(db, payload.tool_id)
        if tool is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tool must exist when provided.",
            )

    approval_request = approval_repository.create(
        db,
        {
            "task_id": payload.task_id,
            "agent_id": payload.agent_id,
            "tool_id": payload.tool_id,
            "requested_action": payload.requested_action,
            "risk_level": payload.risk_level,
            "status": "pending",
            "request_payload": payload.request_payload,
            "decision_reason": None,
            "decided_by": None,
            "decided_at": None,
        },
    )
    task_repository.update_status(db, task, "waiting_approval")
    log_service.record_activity(
        db,
        actor_type="agent",
        actor_id=agent.id,
        request_id=task.request_id,
        event_type="approval.created",
        message="Approval request created.",
        metadata_json={"approval_id": str(approval_request.id), "risk_level": payload.risk_level},
    )
    db.commit()
    db.refresh(approval_request)
    return serialize_approval(approval_request)


def list_approval_requests(db: Session, *, owner_id: uuid.UUID) -> list[ApprovalRequestResponse]:
    approvals = approval_repository.list_by_owner(db, owner_id)
    return [serialize_approval(item) for item in approvals]


def list_pending_approvals(db: Session, *, owner_id: uuid.UUID) -> list[ApprovalRequestResponse]:
    approvals = approval_repository.list_pending_by_owner(db, owner_id)
    return [serialize_approval(item) for item in approvals]


def get_approval_request(
    db: Session,
    *,
    owner_id: uuid.UUID,
    approval_id: uuid.UUID,
) -> ApprovalRequestResponse:
    approval_request = approval_repository.get_by_id(db, approval_id)
    if approval_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found.",
        )
    validate_owner_access(db, owner_id=owner_id, approval_request=approval_request)
    return serialize_approval(approval_request)


def approve_request(
    db: Session,
    *,
    owner_id: uuid.UUID,
    approval_id: uuid.UUID,
    decided_by: uuid.UUID,
    payload: ApprovalDecisionRequest,
) -> ApprovalRequestResponse:
    approval_request = approval_repository.get_by_id(db, approval_id)
    if approval_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found.",
        )
    validate_owner_access(db, owner_id=owner_id, approval_request=approval_request)

    if approval_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending approval requests can be approved.",
        )

    approval_repository.update_decision(
        db,
        approval_request,
        status="approved",
        decision_reason=payload.decision_reason,
        decided_by=decided_by,
        decided_at=datetime.now(UTC),
    )
    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=decided_by,
        request_id=None,
        event_type="approval.approved",
        message="Approval request approved.",
        metadata_json={"approval_id": str(approval_request.id)},
    )
    log_service.record_audit(
        db,
        user_id=decided_by,
        action="approve",
        entity_type="approval_request",
        entity_id=approval_request.id,
        before_data={"status": "pending"},
        after_data={"status": "approved", "decision_reason": payload.decision_reason},
        ip_address=None,
    )
    db.commit()
    db.refresh(approval_request)
    return serialize_approval(approval_request)


def reject_request(
    db: Session,
    *,
    owner_id: uuid.UUID,
    approval_id: uuid.UUID,
    decided_by: uuid.UUID,
    payload: ApprovalDecisionRequest,
) -> ApprovalRequestResponse:
    approval_request = approval_repository.get_by_id(db, approval_id)
    if approval_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found.",
        )
    validate_owner_access(db, owner_id=owner_id, approval_request=approval_request)

    if approval_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending approval requests can be rejected.",
        )

    approval_repository.update_decision(
        db,
        approval_request,
        status="rejected",
        decision_reason=payload.decision_reason,
        decided_by=decided_by,
        decided_at=datetime.now(UTC),
    )
    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=decided_by,
        request_id=None,
        event_type="approval.rejected",
        message="Approval request rejected.",
        metadata_json={"approval_id": str(approval_request.id)},
    )
    log_service.record_audit(
        db,
        user_id=decided_by,
        action="reject",
        entity_type="approval_request",
        entity_id=approval_request.id,
        before_data={"status": "pending"},
        after_data={"status": "rejected", "decision_reason": payload.decision_reason},
        ip_address=None,
    )
    db.commit()
    db.refresh(approval_request)
    return serialize_approval(approval_request)
