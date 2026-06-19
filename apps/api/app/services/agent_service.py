import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.subscription_plans import (
    ROLE_ADMIN,
    ROLE_USER,
    SubscriptionPlanLimits,
    get_subscription_plan_limits,
)
from app.repositories import (
    agent_instruction_repository,
    agent_repository,
    model_provider_repository,
    user_repository,
)
from app.schemas.agent import (
    AgentCreate,
    AgentInstructionCreate,
    AgentInstructionResponse,
    AgentResponse,
    AgentUpdate,
)
from app.services import log_service


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


def _agent_snapshot(agent) -> dict:
    return {
        "name": agent.name,
        "slug": agent.slug,
        "description": agent.description,
        "role_description": agent.role_description,
        "default_model_provider_id": str(agent.default_model_provider_id) if agent.default_model_provider_id else None,
        "default_model_name": agent.default_model_name,
        "status": agent.status,
        "max_steps": agent.max_steps,
        "max_runtime_seconds": agent.max_runtime_seconds,
        "max_token_budget": agent.max_token_budget,
        "requires_approval_by_default": agent.requires_approval_by_default,
    }


def enforce_agent_quota(db: Session, *, owner_id: uuid.UUID) -> None:
    user = user_repository.get_by_id(db, owner_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if user.role == ROLE_ADMIN:
        return

    if user.role != ROLE_USER:
        return

    limits: SubscriptionPlanLimits = get_subscription_plan_limits(user.subscription_plan)
    current_agent_count = agent_repository.count_by_owner(db, owner_id)
    if current_agent_count < limits.max_agents:
        return

    plan_name = user.subscription_plan.capitalize()
    if user.subscription_plan == "free":
        upgrade_text = "Upgrade to Pro or Executive to create more."
    elif user.subscription_plan == "pro":
        upgrade_text = "Upgrade to Executive to create more."
    else:
        upgrade_text = "Delete an existing agent to create another."

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            f"Your {plan_name} plan allows up to {limits.max_agents} agents. "
            f"{upgrade_text}"
        ),
    )


def create_agent(db: Session, *, owner_id: uuid.UUID, payload: AgentCreate) -> AgentResponse:
    enforce_agent_quota(db, owner_id=owner_id)
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
    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=owner_id,
        request_id=None,
        event_type="agent.created",
        message="Agent created.",
        metadata_json={
            "agent_id": str(agent.id),
            "slug": agent.slug,
            "status": agent.status,
            "default_model_provider_id": str(agent.default_model_provider_id) if agent.default_model_provider_id else None,
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

    before_data = _agent_snapshot(agent)
    agent = agent_repository.update(db, agent, update_data)
    after_data = _agent_snapshot(agent)
    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=owner_id,
        request_id=None,
        event_type="agent.updated",
        message="Agent updated.",
        metadata_json={
            "agent_id": str(agent.id),
            "slug": agent.slug,
            "status": agent.status,
        },
    )
    log_service.record_audit(
        db,
        user_id=owner_id,
        action="update",
        entity_type="agent",
        entity_id=agent.id,
        before_data=before_data,
        after_data=after_data,
        ip_address=None,
    )
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
    before_data = _agent_snapshot(agent)
    agent = agent_repository.soft_delete(db, agent, datetime.now(UTC))
    after_data = _agent_snapshot(agent)
    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=owner_id,
        request_id=None,
        event_type="agent.deactivated",
        message="Agent deactivated.",
        metadata_json={
            "agent_id": str(agent.id),
            "slug": agent.slug,
            "status": agent.status,
        },
    )
    log_service.record_audit(
        db,
        user_id=owner_id,
        action="deactivate",
        entity_type="agent",
        entity_id=agent.id,
        before_data=before_data,
        after_data=after_data,
        ip_address=None,
    )
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
    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=owner_id,
        request_id=None,
        event_type="agent.instruction.created",
        message="Agent instruction version created.",
        metadata_json={
            "agent_id": str(agent.id),
            "instruction_id": str(instruction.id),
            "version": version,
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
