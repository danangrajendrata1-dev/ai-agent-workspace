import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import (
    agent_instruction_repository,
    agent_repository,
    model_provider_repository,
)
from app.schemas.agent import (
    AgentCreate,
    AgentInstructionCreate,
    AgentInstructionResponse,
    AgentResponse,
    AgentUpdate,
)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:120] or "agent"


def ensure_unique_slug(
    db: Session,
    *,
    slug: str,
    current_agent_id: uuid.UUID | None = None,
) -> str:
    existing = agent_repository.get_by_slug(db, slug)
    if existing is None or existing.id == current_agent_id:
        return slug
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Agent slug is already in use.",
    )


def validate_default_model_provider(db: Session, provider_id: uuid.UUID | None) -> None:
    if provider_id is None:
        return
    provider = model_provider_repository.get_active_by_id(db, provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default model provider must reference an active provider.",
        )


def serialize_agent(agent) -> AgentResponse:
    return AgentResponse.model_validate(agent)


def serialize_instruction(instruction) -> AgentInstructionResponse:
    return AgentInstructionResponse.model_validate(instruction)


def create_agent(db: Session, *, owner_id: uuid.UUID, payload: AgentCreate) -> AgentResponse:
    validate_default_model_provider(db, payload.default_model_provider_id)
    slug = ensure_unique_slug(db, slug=slugify(payload.slug or payload.name))

    agent_data = payload.model_dump(exclude={"instruction_text"})
    agent_data["owner_id"] = owner_id
    agent_data["slug"] = slug

    agent = agent_repository.create(db, agent_data)
    agent_instruction_repository.create_instruction(
        db,
        {
            "agent_id": agent.id,
            "instruction_text": payload.instruction_text,
            "version": 1,
            "is_active": True,
        },
    )
    db.commit()
    db.refresh(agent)
    return serialize_agent(agent)


def list_agents(db: Session, *, owner_id: uuid.UUID) -> list[AgentResponse]:
    agents = agent_repository.list_by_owner(db, owner_id)
    return [serialize_agent(agent) for agent in agents]


def get_agent(db: Session, *, owner_id: uuid.UUID, agent_id: uuid.UUID) -> AgentResponse:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )
    return serialize_agent(agent)


def update_agent(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    payload: AgentUpdate,
) -> AgentResponse:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if "default_model_provider_id" in update_data:
        validate_default_model_provider(db, update_data["default_model_provider_id"])

    if "slug" in update_data or "name" in update_data:
        source_slug = update_data.get("slug") or update_data.get("name") or agent.slug
        update_data["slug"] = ensure_unique_slug(
            db,
            slug=slugify(source_slug),
            current_agent_id=agent.id,
        )

    agent = agent_repository.update(db, agent, update_data)
    db.commit()
    db.refresh(agent)
    return serialize_agent(agent)


def deactivate_agent(db: Session, *, owner_id: uuid.UUID, agent_id: uuid.UUID) -> AgentResponse:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )
    agent = agent_repository.soft_delete(db, agent, datetime.now(UTC))
    db.commit()
    db.refresh(agent)
    return serialize_agent(agent)


def create_instruction_version(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    payload: AgentInstructionCreate,
) -> AgentInstructionResponse:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    agent_instruction_repository.deactivate_active_instructions(db, agent.id)
    version = agent_instruction_repository.get_next_version(db, agent.id)
    instruction = agent_instruction_repository.create_instruction(
        db,
        {
            "agent_id": agent.id,
            "instruction_text": payload.instruction_text,
            "version": version,
            "is_active": True,
        },
    )
    db.commit()
    db.refresh(instruction)
    return serialize_instruction(instruction)


def get_agent_instructions(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
) -> list[AgentInstructionResponse]:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )
    instructions = agent_instruction_repository.list_instructions_by_agent(db, agent.id)
    return [serialize_instruction(instruction) for instruction in instructions]
