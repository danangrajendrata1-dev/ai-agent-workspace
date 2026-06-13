import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import agent_repository, agent_tool_repository, tool_repository
from app.schemas.tool import (
    AgentToolAssignRequest,
    AgentToolResponse,
    ToolCreate,
    ToolResponse,
    ToolUpdate,
)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:150] or "tool"


def ensure_unique_slug(
    db: Session,
    *,
    slug: str,
    current_tool_id: uuid.UUID | None = None,
) -> str:
    existing = tool_repository.get_by_slug(db, slug)
    if existing is None or existing.id == current_tool_id:
        return slug
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tool slug is already in use.",
    )


def validate_tool_config(tool_data: dict) -> dict:
    normalized = dict(tool_data)
    risk_level = normalized.get("risk_level")
    tool_type = normalized.get("tool_type")
    source_type = normalized.get("source_type")

    if risk_level == "high":
        normalized["approval_required"] = True

    if risk_level == "critical":
        normalized["approval_required"] = True
        normalized["status"] = "disabled"

    if tool_type == "github" or source_type == "github":
        normalized["approval_required"] = True
        if normalized.get("status") != "disabled":
            normalized["status"] = "disabled"

    return normalized


def validate_agent_tool_permission(assignment_data: dict) -> None:
    permission_mode = assignment_data.get("permission_mode")
    is_enabled = assignment_data.get("is_enabled")
    if permission_mode == "block" and is_enabled:
        assignment_data["is_enabled"] = False


def serialize_tool(tool) -> ToolResponse:
    return ToolResponse.model_validate(tool)


def serialize_assignment(assignment) -> AgentToolResponse:
    return AgentToolResponse(
        id=assignment.id,
        agent_id=assignment.agent_id,
        tool_id=assignment.tool_id,
        is_enabled=assignment.is_enabled,
        permission_mode=assignment.permission_mode,
        override_approval_required=assignment.override_approval_required,
        created_at=assignment.created_at,
        tool=serialize_tool(assignment.tool),
    )


def create_tool(db: Session, payload: ToolCreate) -> ToolResponse:
    tool_data = validate_tool_config(payload.model_dump())
    tool_data["slug"] = ensure_unique_slug(db, slug=slugify(payload.slug or payload.name))

    tool = tool_repository.create(db, tool_data)
    db.commit()
    db.refresh(tool)
    return serialize_tool(tool)


def list_tools(db: Session) -> list[ToolResponse]:
    tools = tool_repository.list(db)
    return [serialize_tool(tool) for tool in tools]


def get_tool(db: Session, tool_id: uuid.UUID) -> ToolResponse:
    tool = tool_repository.get_by_id(db, tool_id)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        )
    return serialize_tool(tool)


def update_tool(db: Session, tool_id: uuid.UUID, payload: ToolUpdate) -> ToolResponse:
    tool = tool_repository.get_by_id(db, tool_id)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    candidate = {
        "name": update_data.get("name", tool.name),
        "slug": update_data.get("slug", tool.slug),
        "description": update_data.get("description", tool.description),
        "tool_type": update_data.get("tool_type", tool.tool_type),
        "source_type": update_data.get("source_type", tool.source_type),
        "source_id": update_data.get("source_id", tool.source_id),
        "input_schema": update_data.get("input_schema", tool.input_schema),
        "output_schema": update_data.get("output_schema", tool.output_schema),
        "risk_level": update_data.get("risk_level", tool.risk_level),
        "approval_required": update_data.get("approval_required", tool.approval_required),
        "timeout_seconds": update_data.get("timeout_seconds", tool.timeout_seconds),
        "rate_limit_per_hour": update_data.get("rate_limit_per_hour", tool.rate_limit_per_hour),
        "status": update_data.get("status", tool.status),
    }
    candidate = validate_tool_config(candidate)

    if "slug" in update_data or "name" in update_data:
        source_slug = update_data.get("slug") or update_data.get("name") or tool.slug
        candidate["slug"] = ensure_unique_slug(
            db,
            slug=slugify(source_slug),
            current_tool_id=tool.id,
        )

    tool = tool_repository.update(db, tool, candidate)
    db.commit()
    db.refresh(tool)
    return serialize_tool(tool)


def deactivate_tool(db: Session, tool_id: uuid.UUID) -> ToolResponse:
    tool = tool_repository.get_by_id(db, tool_id)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        )
    tool = tool_repository.soft_delete(db, tool, datetime.now(UTC))
    db.commit()
    db.refresh(tool)
    return serialize_tool(tool)


def assign_tool_to_agent(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    payload: AgentToolAssignRequest,
) -> AgentToolResponse:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    tool = tool_repository.get_by_id(db, payload.tool_id)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        )

    assignment_data = payload.model_dump()
    validate_agent_tool_permission(assignment_data)

    assignment = agent_tool_repository.get_assignment(db, agent.id, tool.id)
    if assignment is not None:
        assignment = agent_tool_repository.update_assignment(db, assignment, assignment_data)
        db.commit()
        db.refresh(assignment)
        assignment = agent_tool_repository.get_assignment(db, agent.id, tool.id)
        return serialize_assignment(assignment)

    assignment = agent_tool_repository.assign_tool_to_agent(
        db,
        {
            "agent_id": agent.id,
            "tool_id": tool.id,
            **assignment_data,
        },
    )
    db.commit()
    db.refresh(assignment)
    assignment = agent_tool_repository.get_assignment(db, agent.id, tool.id)
    return serialize_assignment(assignment)


def remove_tool_from_agent(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    tool_id: uuid.UUID,
) -> None:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    assignment = agent_tool_repository.get_assignment(db, agent.id, tool_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent tool assignment not found.",
        )

    agent_tool_repository.remove_tool_from_agent(db, assignment)
    db.commit()


def list_agent_tools(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
) -> list[AgentToolResponse]:
    agent = agent_repository.get_by_id(db, owner_id, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    assignments = agent_tool_repository.list_agent_tools(db, agent.id)
    return [serialize_assignment(assignment) for assignment in assignments]
