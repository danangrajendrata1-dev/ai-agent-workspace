import uuid

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.agent import (
    AgentCreate,
    AgentAvatarUploadResponse,
    AgentInstructionCreate,
    AgentInstructionResponse,
    AgentListResponse,
    AgentRoutingPreviewRequest,
    AgentRoutingPreviewResponse,
    AgentResponse,
    AgentUpdate,
    TaskDraftRequest,
    TaskDraftResponse,
)
from app.schemas.agent_chat import AgentChatRequest, AgentChatResponse
from app.services import agent_chat_service, agent_routing_service, agent_service, agent_task_draft_service
from app.services.agent_avatar_service import get_agent_avatar_content, read_upload_file_bytes, delete_agent_avatar, upload_agent_avatar


router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    payload: AgentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return agent_service.create_agent(db, owner_id=current_user.id, payload=payload)


@router.get("", response_model=AgentListResponse)
def list_agents(db: Session = Depends(get_db), current_user=Depends(require_owner)):
    return AgentListResponse(items=agent_service.list_agents(db, owner_id=current_user.id))


@router.post("/task-draft", response_model=TaskDraftResponse)
def create_agent_task_draft(
    payload: TaskDraftRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return agent_task_draft_service.create_agent_task_draft(
        db,
        current_user=current_user,
        task_text=payload.task_text,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return agent_service.get_agent(db, owner_id=current_user.id, agent_id=agent_id)


@router.post("/{agent_id}/avatar", response_model=AgentAvatarUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_avatar(
    agent_id: uuid.UUID,
    file: UploadFile = File(...),
    avatar_kind: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    file_bytes = await read_upload_file_bytes(file, max_bytes=get_settings().agent_avatar_max_bytes)
    return upload_agent_avatar(
        db,
        owner_id=current_user.id,
        agent_id=agent_id,
        data=file_bytes,
        original_filename=file.filename,
        declared_content_type=file.content_type,
        avatar_kind=avatar_kind,
    )


@router.get("/{agent_id}/avatar/content")
def get_avatar_content(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    content, content_type = get_agent_avatar_content(db, owner_id=current_user.id, agent_id=agent_id)
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Cache-Control": "private, max-age=3600",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete("/{agent_id}/avatar", response_model=AgentResponse)
def remove_avatar(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return delete_agent_avatar(db, owner_id=current_user.id, agent_id=agent_id)


@router.post("/{agent_id}/chat", response_model=AgentChatResponse)
def chat_with_agent(
    agent_id: uuid.UUID,
    payload: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return agent_chat_service.chat_with_agent(
        db,
        owner_id=current_user.id,
        agent_id=agent_id,
        payload=payload,
        current_user=current_user,
    )


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: uuid.UUID,
    payload: AgentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return agent_service.update_agent(
        db,
        owner_id=current_user.id,
        agent_id=agent_id,
        payload=payload,
    )


@router.post("/{agent_id}/deactivate", response_model=AgentResponse)
def deactivate_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return agent_service.deactivate_agent(db, owner_id=current_user.id, agent_id=agent_id)


@router.get("/{agent_id}/instructions", response_model=list[AgentInstructionResponse])
def get_agent_instructions(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return agent_service.get_agent_instructions(
        db,
        owner_id=current_user.id,
        agent_id=agent_id,
    )


@router.post(
    "/{agent_id}/instructions",
    response_model=AgentInstructionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_instruction_version(
    agent_id: uuid.UUID,
    payload: AgentInstructionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return agent_service.create_instruction_version(
        db,
        owner_id=current_user.id,
        agent_id=agent_id,
        payload=payload,
    )


@router.post("/routing-preview", response_model=AgentRoutingPreviewResponse)
def preview_agent_routing(
    payload: AgentRoutingPreviewRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return agent_routing_service.preview_agent_routing(
        db,
        current_user=current_user,
        task_text=payload.task_text,
    )
