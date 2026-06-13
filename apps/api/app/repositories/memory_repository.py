import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory


def create(db: Session, memory_data: dict) -> Memory:
    memory = Memory(**memory_data)
    db.add(memory)
    db.flush()
    return memory


def get_by_id(db: Session, owner_id: uuid.UUID, memory_id: uuid.UUID) -> Memory | None:
    statement = select(Memory).where(
        Memory.id == memory_id,
        Memory.owner_id == owner_id,
        Memory.deleted_at.is_(None),
    )
    return db.execute(statement).scalar_one_or_none()


def list_by_owner(db: Session, owner_id: uuid.UUID) -> list[Memory]:
    statement = (
        select(Memory)
        .where(Memory.owner_id == owner_id, Memory.deleted_at.is_(None))
        .order_by(Memory.created_at.desc())
    )
    return list(db.execute(statement).scalars().all())


def list_by_agent(db: Session, owner_id: uuid.UUID, agent_id: uuid.UUID) -> list[Memory]:
    statement = (
        select(Memory)
        .where(
            Memory.owner_id == owner_id,
            Memory.agent_id == agent_id,
            Memory.deleted_at.is_(None),
        )
        .order_by(Memory.created_at.desc())
    )
    return list(db.execute(statement).scalars().all())


def update(db: Session, memory: Memory, memory_data: dict) -> Memory:
    for field, value in memory_data.items():
        setattr(memory, field, value)
    db.add(memory)
    db.flush()
    return memory


def soft_delete(db: Session, memory: Memory, deleted_at) -> Memory:
    memory.deleted_at = deleted_at
    db.add(memory)
    db.flush()
    return memory
