import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Agent


def create(db: Session, agent_data: dict) -> Agent:
    agent = Agent(**agent_data)
    db.add(agent)
    db.flush()
    return agent


def get_by_id(db: Session, owner_id: uuid.UUID, agent_id: uuid.UUID) -> Agent | None:
    statement = select(Agent).where(
        Agent.id == agent_id,
        Agent.owner_id == owner_id,
        Agent.deleted_at.is_(None),
    )
    return db.execute(statement).scalar_one_or_none()


def get_by_id_for_admin(db: Session, agent_id: uuid.UUID) -> Agent | None:
    statement = select(Agent).where(
        Agent.id == agent_id,
        Agent.deleted_at.is_(None),
    )
    return db.execute(statement).scalar_one_or_none()


def get_by_slug(db: Session, slug: str) -> Agent | None:
    statement = select(Agent).where(
        Agent.slug == slug,
        Agent.deleted_at.is_(None),
    )
    return db.execute(statement).scalar_one_or_none()


def list_by_owner(db: Session, owner_id: uuid.UUID) -> list[Agent]:
    statement = (
        select(Agent)
        .where(Agent.owner_id == owner_id, Agent.deleted_at.is_(None))
        .order_by(Agent.created_at.desc())
    )
    return list(db.execute(statement).scalars().all())


def count_by_owner(db: Session, owner_id: uuid.UUID) -> int:
    statement = select(func.count(Agent.id)).where(
        Agent.owner_id == owner_id,
        Agent.deleted_at.is_(None),
    )
    return db.execute(statement).scalar_one()


def update(db: Session, agent: Agent, agent_data: dict) -> Agent:
    for field, value in agent_data.items():
        setattr(agent, field, value)
    db.add(agent)
    db.flush()
    return agent


def soft_delete(db: Session, agent: Agent, deleted_at) -> Agent:
    agent.deleted_at = deleted_at
    agent.status = "inactive"
    db.add(agent)
    db.flush()
    return agent


def set_status(db: Session, agent: Agent, status: str) -> Agent:
    agent.status = status
    db.add(agent)
    db.flush()
    return agent
