import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tool import Tool


def create(db: Session, tool_data: dict) -> Tool:
    tool = Tool(**tool_data)
    db.add(tool)
    db.flush()
    return tool


def get_by_id(db: Session, tool_id: uuid.UUID) -> Tool | None:
    statement = select(Tool).where(Tool.id == tool_id, Tool.deleted_at.is_(None))
    return db.execute(statement).scalar_one_or_none()


def get_by_slug(db: Session, slug: str) -> Tool | None:
    statement = select(Tool).where(Tool.slug == slug, Tool.deleted_at.is_(None))
    return db.execute(statement).scalar_one_or_none()


def list(db: Session) -> list[Tool]:
    statement = select(Tool).where(Tool.deleted_at.is_(None)).order_by(Tool.created_at.desc())
    return db.execute(statement).scalars().all()


def update(db: Session, tool: Tool, tool_data: dict) -> Tool:
    for field, value in tool_data.items():
        setattr(tool, field, value)
    db.add(tool)
    db.flush()
    return tool


def soft_delete(db: Session, tool: Tool, deleted_at) -> Tool:
    tool.deleted_at = deleted_at
    tool.status = "disabled"
    db.add(tool)
    db.flush()
    return tool


def set_status(db: Session, tool: Tool, status: str) -> Tool:
    tool.status = status
    db.add(tool)
    db.flush()
    return tool
