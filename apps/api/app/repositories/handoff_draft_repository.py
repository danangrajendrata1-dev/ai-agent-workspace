import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.handoff_draft import HandoffDraft


def create(db: Session, draft_data: dict) -> HandoffDraft:
    draft = HandoffDraft(**draft_data)
    db.add(draft)
    db.flush()
    return draft


def get_by_id(db: Session, draft_id: uuid.UUID) -> HandoffDraft | None:
    statement = select(HandoffDraft).where(HandoffDraft.id == draft_id)
    return db.execute(statement).scalar_one_or_none()


def get_by_id_for_owner(db: Session, draft_id: uuid.UUID, owner_id: uuid.UUID) -> HandoffDraft | None:
    statement = select(HandoffDraft).where(
        HandoffDraft.id == draft_id,
        HandoffDraft.owner_id == owner_id,
    )
    return db.execute(statement).scalar_one_or_none()


def list_by_owner(db: Session, owner_id: uuid.UUID, *, limit: int = 20, offset: int = 0) -> list[HandoffDraft]:
    statement = (
        select(HandoffDraft)
        .where(HandoffDraft.owner_id == owner_id)
        .order_by(HandoffDraft.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(statement).scalars().all())


def list_all(db: Session, *, limit: int = 20, offset: int = 0) -> list[HandoffDraft]:
    statement = select(HandoffDraft).order_by(HandoffDraft.created_at.desc()).limit(limit).offset(offset)
    return list(db.execute(statement).scalars().all())


def update(db: Session, draft: HandoffDraft, draft_data: dict) -> HandoffDraft:
    for field, value in draft_data.items():
        setattr(draft, field, value)
    db.add(draft)
    db.flush()
    return draft
