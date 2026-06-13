import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.skill import (
    AgentSkillAssignRequest,
    AgentSkillResponse,
    SkillCreate,
    SkillListResponse,
    SkillResponse,
    SkillUpdate,
)
from app.services import skill_service


router = APIRouter(tags=["skills"])


@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(
    payload: SkillCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return skill_service.create_skill(db, payload)


@router.get("/skills", response_model=SkillListResponse)
def list_skills(db: Session = Depends(get_db), current_user=Depends(require_owner)):
    return SkillListResponse(items=skill_service.list_skills(db))


@router.get("/skills/{skill_id}", response_model=SkillResponse)
def get_skill(
    skill_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return skill_service.get_skill(db, skill_id)


@router.patch("/skills/{skill_id}", response_model=SkillResponse)
def update_skill(
    skill_id: uuid.UUID,
    payload: SkillUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return skill_service.update_skill(db, skill_id, payload)


@router.post("/skills/{skill_id}/deactivate", response_model=SkillResponse)
def deactivate_skill(
    skill_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return skill_service.deactivate_skill(db, skill_id)


@router.post(
    "/agents/{agent_id}/skills",
    response_model=AgentSkillResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_skill_to_agent(
    agent_id: uuid.UUID,
    payload: AgentSkillAssignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return skill_service.assign_skill_to_agent(
        db,
        owner_id=current_user.id,
        agent_id=agent_id,
        payload=payload,
    )


@router.get("/agents/{agent_id}/skills", response_model=list[AgentSkillResponse])
def list_agent_skills(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return skill_service.list_agent_skills(db, owner_id=current_user.id, agent_id=agent_id)


@router.delete("/agents/{agent_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_skill_from_agent(
    agent_id: uuid.UUID,
    skill_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    skill_service.remove_skill_from_agent(
        db,
        owner_id=current_user.id,
        agent_id=agent_id,
        skill_id=skill_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
