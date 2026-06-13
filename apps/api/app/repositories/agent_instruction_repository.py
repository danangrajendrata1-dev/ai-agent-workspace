import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.agent_instruction import AgentInstruction


def create_instruction(db: Session, instruction_data: dict) -> AgentInstruction:
    instruction = AgentInstruction(**instruction_data)
    db.add(instruction)
    db.flush()
    return instruction


def get_active_instruction(db: Session, agent_id: uuid.UUID) -> AgentInstruction | None:
    statement = select(AgentInstruction).where(
        AgentInstruction.agent_id == agent_id,
        AgentInstruction.is_active.is_(True),
    )
    return db.execute(statement).scalar_one_or_none()


def list_instructions_by_agent(db: Session, agent_id: uuid.UUID) -> list[AgentInstruction]:
    statement = (
        select(AgentInstruction)
        .where(AgentInstruction.agent_id == agent_id)
        .order_by(AgentInstruction.version.desc())
    )
    return list(db.execute(statement).scalars().all())


def deactivate_active_instructions(db: Session, agent_id: uuid.UUID) -> None:
    statement = (
        update(AgentInstruction)
        .where(
            AgentInstruction.agent_id == agent_id,
            AgentInstruction.is_active.is_(True),
        )
        .values(is_active=False)
    )
    db.execute(statement)


def get_next_version(db: Session, agent_id: uuid.UUID) -> int:
    statement = select(func.max(AgentInstruction.version)).where(
        AgentInstruction.agent_id == agent_id
    )
    current = db.execute(statement).scalar_one()
    return (current or 0) + 1
