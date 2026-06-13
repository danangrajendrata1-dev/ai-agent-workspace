import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.log import (
    ActivityLogListResponse,
    ActivityLogResponse,
    AuditLogListResponse,
    AuditLogResponse,
    ModelUsageLogListResponse,
    ModelUsageLogResponse,
    ToolCallListResponse,
    ToolCallResponse,
)
from app.services import log_service


router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/activity", response_model=ActivityLogListResponse)
def list_activity_logs(
    request_id: str | None = None,
    event_type: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return {"items": log_service.list_activity_logs(db, request_id=request_id, event_type=event_type, limit=limit)}


@router.get("/activity/{log_id}", response_model=ActivityLogResponse)
def get_activity_log(
    log_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return log_service.get_activity_log(db, log_id)


@router.get("/audit", response_model=AuditLogListResponse)
def list_audit_logs(
    entity_type: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return {"items": log_service.list_audit_logs(db, user_id=current_user.id, entity_type=entity_type, limit=limit)}


@router.get("/audit/{log_id}", response_model=AuditLogResponse)
def get_audit_log(
    log_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return log_service.get_audit_log(db, log_id)


@router.get("/tool-calls", response_model=ToolCallListResponse)
def list_tool_calls(
    task_id: uuid.UUID | None = None,
    tool_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return {
        "items": log_service.list_tool_calls(
            db,
            owner_id=current_user.id,
            task_id=task_id,
            tool_id=tool_id,
            status=status,
            limit=limit,
        )
    }


@router.get("/tool-calls/{tool_call_id}", response_model=ToolCallResponse)
def get_tool_call(
    tool_call_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return log_service.get_tool_call(db, owner_id=current_user.id, log_id=tool_call_id)


@router.get("/model-usage", response_model=ModelUsageLogListResponse)
def list_model_usage_logs(
    provider_id: uuid.UUID | None = None,
    agent_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return {
        "items": log_service.list_model_usage_logs(
            db,
            owner_id=current_user.id,
            provider_id=provider_id,
            agent_id=agent_id,
            task_id=task_id,
            status=status,
            limit=limit,
        )
    }


@router.get("/model-usage/{usage_log_id}", response_model=ModelUsageLogResponse)
def get_model_usage_log(
    usage_log_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return log_service.get_model_usage_log(db, owner_id=current_user.id, log_id=usage_log_id)
