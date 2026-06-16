import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.session import SessionDeleteResponse, SessionDetail, SessionListResponse
from app.services import session_service


router = APIRouter(tags=["sessions"])


@router.get("/sessions", response_model=SessionListResponse)
def list_sessions(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return session_service.list_chat_sessions(
        db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return session_service.get_chat_session(
        db,
        user_id=current_user.id,
        session_id=session_id,
    )


@router.delete("/sessions/{session_id}", response_model=SessionDeleteResponse)
def delete_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return session_service.delete_chat_session(
        db,
        user_id=current_user.id,
        session_id=session_id,
    )
