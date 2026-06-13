import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.memory import MemoryCreate, MemoryListResponse, MemoryResponse, MemoryUpdate
from app.services import memory_service


router = APIRouter(tags=["memories"])


@router.post("/memories", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
def create_memory(
    payload: MemoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return memory_service.create_memory(db, owner_id=current_user.id, payload=payload)


@router.get("/memories", response_model=MemoryListResponse)
def list_memories(db: Session = Depends(get_db), current_user=Depends(require_owner)):
    return MemoryListResponse(items=memory_service.list_memories(db, owner_id=current_user.id))


@router.get("/memories/{memory_id}", response_model=MemoryResponse)
def get_memory(
    memory_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return memory_service.get_memory(db, owner_id=current_user.id, memory_id=memory_id)


@router.patch("/memories/{memory_id}", response_model=MemoryResponse)
def update_memory(
    memory_id: uuid.UUID,
    payload: MemoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return memory_service.update_memory(
        db,
        owner_id=current_user.id,
        memory_id=memory_id,
        payload=payload,
    )


@router.delete("/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    memory_service.delete_memory(db, owner_id=current_user.id, memory_id=memory_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/agents/{agent_id}/memories", response_model=list[MemoryResponse])
def list_agent_memories(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return memory_service.list_agent_memories(db, owner_id=current_user.id, agent_id=agent_id)
