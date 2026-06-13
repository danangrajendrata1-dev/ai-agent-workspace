import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.task import AgentChatRequest, TaskDetailResponse, TaskListResponse
from app.services import task_service


router = APIRouter(tags=["tasks"])


@router.post(
    "/agents/{agent_id}/chat",
    response_model=TaskDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agent_chat_task(
    agent_id: uuid.UUID,
    payload: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return task_service.create_agent_chat_task(
        db,
        owner_id=current_user.id,
        agent_id=agent_id,
        payload=payload,
    )


@router.get("/tasks", response_model=TaskListResponse)
def list_tasks(db: Session = Depends(get_db), current_user=Depends(require_owner)):
    return TaskListResponse(items=task_service.list_tasks(db, owner_id=current_user.id))


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
def get_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return task_service.get_task(db, owner_id=current_user.id, task_id=task_id)


@router.get("/agents/{agent_id}/tasks", response_model=TaskListResponse)
def list_agent_tasks(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return TaskListResponse(
        items=task_service.list_agent_tasks(db, owner_id=current_user.id, agent_id=agent_id)
    )
