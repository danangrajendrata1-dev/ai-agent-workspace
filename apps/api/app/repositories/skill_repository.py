import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.skill import Skill


def create(db: Session, skill_data: dict) -> Skill:
    skill = Skill(**skill_data)
    db.add(skill)
    db.flush()
    return skill


def get_by_id(db: Session, skill_id: uuid.UUID) -> Skill | None:
    statement = select(Skill).where(Skill.id == skill_id, Skill.deleted_at.is_(None))
    return db.execute(statement).scalar_one_or_none()


def get_by_slug(db: Session, slug: str) -> Skill | None:
    statement = select(Skill).where(Skill.slug == slug, Skill.deleted_at.is_(None))
    return db.execute(statement).scalar_one_or_none()


def list(db: Session) -> list[Skill]:
    statement = select(Skill).where(Skill.deleted_at.is_(None)).order_by(Skill.created_at.desc())
    return db.execute(statement).scalars().all()


def update(db: Session, skill: Skill, skill_data: dict) -> Skill:
    for field, value in skill_data.items():
        setattr(skill, field, value)
    db.add(skill)
    db.flush()
    return skill


def soft_delete(db: Session, skill: Skill, deleted_at) -> Skill:
    skill.deleted_at = deleted_at
    skill.status = "disabled"
    db.add(skill)
    db.flush()
    return skill


def set_status(db: Session, skill: Skill, status: str) -> Skill:
    skill.status = status
    db.add(skill)
    db.flush()
    return skill
