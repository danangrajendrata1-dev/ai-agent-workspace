import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import agent_repository, agent_skill_repository, skill_repository
from app.schemas.skill import (
    AgentSkillAssignRequest,
    AgentSkillResponse,
    SkillCreate,
    SkillResponse,
    SkillUpdate,
)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:150] or "skill"


def ensure_unique_slug(
    db: Session,
    *,
    slug: str,
    current_skill_id: uuid.UUID | None = None,
) -> str:
    existing = skill_repository.get_by_slug(db, slug)
    if existing is None or existing.id == current_skill_id:
        return slug
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Skill slug is already in use.",
    )


def validate_skill_payload(source_type: str, source_id: uuid.UUID | None) -> None:
    if source_type == "manual" and source_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manual skills must not include source_id.",
        )


def serialize_skill(skill) -> SkillResponse:
    return SkillResponse.model_validate(skill)


def serialize_assignment(assignment) -> AgentSkillResponse:
    return AgentSkillResponse(
        id=assignment.id,
        agent_id=assignment.agent_id,
        skill_id=assignment.skill_id,
        is_enabled=assignment.is_enabled,
        created_at=assignment.created_at,
        skill=serialize_skill(assignment.skill),
    )


def create_skill(db: Session, payload: SkillCreate) -> SkillResponse:
    validate_skill_payload(payload.source_type, payload.source_id)
    slug = ensure_unique_slug(db, slug=slugify(payload.slug or payload.name))

    skill_data = payload.model_dump()
    skill_data["slug"] = slug

    skill = skill_repository.create(db, skill_data)
    db.commit()
    db.refresh(skill)
    return serialize_skill(skill)


def list_skills(db: Session) -> list[SkillResponse]:
    skills = skill_repository.list(db)
    return [serialize_skill(skill) for skill in skills]


def get_skill(db: Session, skill_id: uuid.UUID) -> SkillResponse:
    skill = skill_repository.get_by_id(db, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )
    return serialize_skill(skill)


def update_skill(db: Session, skill_id: uuid.UUID, payload: SkillUpdate) -> SkillResponse:
    skill = skill_repository.get_by_id(db, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    source_type = update_data.get("source_type", skill.source_type)
    source_id = update_data.get("source_id", skill.source_id)
    validate_skill_payload(source_type, source_id)

    if "slug" in update_data or "name" in update_data:
        source_slug = update_data.get("slug") or update_data.get("name") or skill.slug
        update_data["slug"] = ensure_unique_slug(
            db,
            slug=slugify(source_slug),
            current_skill_id=skill.id,
        )

    skill = skill_repository.update(db, skill, update_data)
    db.commit()
    db.refresh(skill)
    return serialize_skill(skill)


def deactivate_skill(db: Session, skill_id: uuid.UUID) -> SkillResponse:
    skill = skill_repository.get_by_id(db, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )
    skill = skill_repository.soft_delete(db, skill, datetime.now(UTC))
    db.commit()
    db.refresh(skill)
    return serialize_skill(skill)


def assign_skill_to_agent(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    payload: AgentSkillAssignRequest,
) -> AgentSkillResponse:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    skill = skill_repository.get_by_id(db, payload.skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )

    assignment = agent_skill_repository.get_assignment(db, agent.id, skill.id)
    if assignment is not None:
        assignment = assignment
        assignment.is_enabled = payload.is_enabled
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return serialize_assignment(assignment)

    assignment = agent_skill_repository.assign_skill_to_agent(
        db,
        {
            "agent_id": agent.id,
            "skill_id": skill.id,
            "is_enabled": payload.is_enabled,
        },
    )
    db.commit()
    db.refresh(assignment)
    assignment = agent_skill_repository.get_assignment(db, agent.id, skill.id)
    return serialize_assignment(assignment)


def remove_skill_from_agent(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    skill_id: uuid.UUID,
) -> None:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    assignment = agent_skill_repository.get_assignment(db, agent.id, skill_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent skill assignment not found.",
        )

    agent_skill_repository.unassign_skill_from_agent(db, assignment)
    db.commit()


def list_agent_skills(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
) -> list[AgentSkillResponse]:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    assignments = agent_skill_repository.list_agent_skills(db, agent.id)
    return [serialize_assignment(assignment) for assignment in assignments]
