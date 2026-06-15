import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.handoff_draft import (
    HandoffDraftCreateRequest,
    HandoffDraftListResponse,
    HandoffDraftResponse,
)
from app.services import handoff_draft_service


router = APIRouter(prefix="/handoff-drafts", tags=["handoff-drafts"])


@router.post("", response_model=HandoffDraftResponse, status_code=status.HTTP_201_CREATED)
def create_handoff_draft(
    payload: HandoffDraftCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return handoff_draft_service.create_handoff_draft(
        db,
        owner_id=current_user.id,
        payload=payload,
        current_user=current_user,
    )


@router.get("", response_model=HandoffDraftListResponse)
def list_handoff_drafts(
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return handoff_draft_service.list_handoff_drafts(
        db,
        owner_id=current_user.id,
        current_user=current_user,
        limit=limit,
        offset=offset,
    )


@router.get("/{draft_id}", response_model=HandoffDraftResponse)
def get_handoff_draft(
    draft_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return handoff_draft_service.get_handoff_draft(
        db,
        owner_id=current_user.id,
        draft_id=draft_id,
        current_user=current_user,
    )


@router.post("/{draft_id}/archive", response_model=HandoffDraftResponse)
def archive_handoff_draft(
    draft_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return handoff_draft_service.archive_handoff_draft(
        db,
        owner_id=current_user.id,
        draft_id=draft_id,
        current_user=current_user,
    )
