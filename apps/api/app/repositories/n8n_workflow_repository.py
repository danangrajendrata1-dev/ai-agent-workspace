import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.n8n_workflow import N8nWorkflow


def create(db: Session, workflow_data: dict) -> N8nWorkflow:
    workflow = N8nWorkflow(**workflow_data)
    db.add(workflow)
    db.flush()
    return workflow


def get_by_id(db: Session, owner_id: uuid.UUID, workflow_id: uuid.UUID) -> N8nWorkflow | None:
    statement = select(N8nWorkflow).where(
        N8nWorkflow.id == workflow_id,
        N8nWorkflow.owner_id == owner_id,
        N8nWorkflow.deleted_at.is_(None),
    )
    return db.execute(statement).scalar_one_or_none()


def get_by_slug(db: Session, slug: str) -> N8nWorkflow | None:
    statement = select(N8nWorkflow).where(
        N8nWorkflow.slug == slug,
        N8nWorkflow.deleted_at.is_(None),
    )
    return db.execute(statement).scalar_one_or_none()


def list_by_owner(db: Session, owner_id: uuid.UUID) -> list[N8nWorkflow]:
    statement = (
        select(N8nWorkflow)
        .where(N8nWorkflow.owner_id == owner_id, N8nWorkflow.deleted_at.is_(None))
        .order_by(N8nWorkflow.created_at.desc())
    )
    return list(db.execute(statement).scalars().all())


def count_saved_by_owner(db: Session, owner_id: uuid.UUID) -> int:
    statement = select(func.count(N8nWorkflow.id)).where(
        N8nWorkflow.owner_id == owner_id,
        N8nWorkflow.deleted_at.is_(None),
        N8nWorkflow.status != "disabled",
    )
    return db.execute(statement).scalar_one()


def update(db: Session, workflow: N8nWorkflow, workflow_data: dict) -> N8nWorkflow:
    for field, value in workflow_data.items():
        setattr(workflow, field, value)
    db.add(workflow)
    db.flush()
    return workflow


def soft_delete(db: Session, workflow: N8nWorkflow, deleted_at) -> N8nWorkflow:
    workflow.deleted_at = deleted_at
    workflow.status = "disabled"
    db.add(workflow)
    db.flush()
    return workflow
