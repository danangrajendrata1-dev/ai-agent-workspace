import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.agent import (
    AgentCreate,
    AgentInstructionCreate,
    AgentInstructionResponse,
    AgentListResponse,
    AgentResponse,
    AgentUpdate,
)
from app.services import agent_service


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


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return agent_service.get_agent(db, owner_id=current_user.id, agent_id=agent_id)


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
