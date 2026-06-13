import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.agent_tool import AgentTool


def assign_tool_to_agent(db: Session, assignment_data: dict) -> AgentTool:
    assignment = AgentTool(**assignment_data)
    db.add(assignment)
    db.flush()
    return assignment


def remove_tool_from_agent(db: Session, assignment: AgentTool) -> None:
    db.delete(assignment)
    db.flush()


def list_agent_tools(db: Session, agent_id: uuid.UUID) -> list[AgentTool]:
    statement = (
        select(AgentTool)
        .options(joinedload(AgentTool.tool))
        .where(AgentTool.agent_id == agent_id)
        .order_by(AgentTool.created_at.desc())
    )
    return list(db.execute(statement).scalars().all())


def get_assignment(db: Session, agent_id: uuid.UUID, tool_id: uuid.UUID) -> AgentTool | None:
    statement = (
        select(AgentTool)
        .options(joinedload(AgentTool.tool))
        .where(AgentTool.agent_id == agent_id, AgentTool.tool_id == tool_id)
    )
    return db.execute(statement).scalar_one_or_none()


def update_assignment(db: Session, assignment: AgentTool, assignment_data: dict) -> AgentTool:
    for field, value in assignment_data.items():
        setattr(assignment, field, value)
    db.add(assignment)
    db.flush()
    return assignment
