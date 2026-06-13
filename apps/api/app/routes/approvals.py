import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalRequestCreate,
    ApprovalRequestListResponse,
    ApprovalRequestResponse,
)
from app.services import approval_service


router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("", response_model=ApprovalRequestResponse, status_code=status.HTTP_201_CREATED)
def create_approval_request(
    payload: ApprovalRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return approval_service.create_approval_request(
        db,
        owner_id=current_user.id,
        payload=payload,
    )


@router.get("", response_model=ApprovalRequestListResponse)
def list_approval_requests(
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return ApprovalRequestListResponse(
        items=approval_service.list_approval_requests(db, owner_id=current_user.id)
    )


@router.get("/pending", response_model=ApprovalRequestListResponse)
def list_pending_approvals(
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return ApprovalRequestListResponse(
        items=approval_service.list_pending_approvals(db, owner_id=current_user.id)
    )


@router.get("/{approval_id}", response_model=ApprovalRequestResponse)
def get_approval_request(
    approval_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return approval_service.get_approval_request(
        db,
        owner_id=current_user.id,
        approval_id=approval_id,
    )


@router.post("/{approval_id}/approve", response_model=ApprovalRequestResponse)
def approve_request(
    approval_id: uuid.UUID,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return approval_service.approve_request(
        db,
        owner_id=current_user.id,
        approval_id=approval_id,
        decided_by=current_user.id,
        payload=payload,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalRequestResponse)
def reject_request(
    approval_id: uuid.UUID,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return approval_service.reject_request(
        db,
        owner_id=current_user.id,
        approval_id=approval_id,
        decided_by=current_user.id,
        payload=payload,
    )
