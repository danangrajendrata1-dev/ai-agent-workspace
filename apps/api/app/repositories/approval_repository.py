import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approval_request import ApprovalRequest
from app.models.task import Task


def create(db: Session, approval_data: dict) -> ApprovalRequest:
    approval_request = ApprovalRequest(**approval_data)
    db.add(approval_request)
    db.flush()
    return approval_request


def get_by_id(db: Session, approval_id: uuid.UUID) -> ApprovalRequest | None:
    statement = select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    return db.execute(statement).scalar_one_or_none()


def list_by_owner(db: Session, owner_id: uuid.UUID) -> list[ApprovalRequest]:
    statement = (
        select(ApprovalRequest)
        .join(Task, ApprovalRequest.task_id == Task.id)
        .where(Task.owner_id == owner_id)
        .order_by(ApprovalRequest.created_at.desc())
    )
    return list(db.execute(statement).scalars().all())


def list_pending_by_owner(db: Session, owner_id: uuid.UUID) -> list[ApprovalRequest]:
    statement = (
        select(ApprovalRequest)
        .join(Task, ApprovalRequest.task_id == Task.id)
        .where(
            Task.owner_id == owner_id,
            ApprovalRequest.status == "pending",
        )
        .order_by(ApprovalRequest.created_at.desc())
    )
    return list(db.execute(statement).scalars().all())


def update_decision(
    db: Session,
    approval_request: ApprovalRequest,
    *,
    status: str,
    decision_reason: str | None,
    decided_by,
    decided_at,
) -> ApprovalRequest:
    approval_request.status = status
    approval_request.decision_reason = decision_reason
    approval_request.decided_by = decided_by
    approval_request.decided_at = decided_at
    db.add(approval_request)
    db.flush()
    return approval_request


def expire_request(db: Session, approval_request: ApprovalRequest) -> ApprovalRequest:
    approval_request.status = "expired"
    db.add(approval_request)
    db.flush()
    return approval_request
