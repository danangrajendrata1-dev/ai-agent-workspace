import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow_consent import WorkflowConsent


def get_consent(
    db: Session,
    *,
    user_id: uuid.UUID,
    template_id: str,
    template_version: str,
) -> WorkflowConsent | None:
    statement = select(WorkflowConsent).where(
        WorkflowConsent.user_id == user_id,
        WorkflowConsent.template_id == template_id,
        WorkflowConsent.template_version == template_version,
    )
    return db.execute(statement).scalar_one_or_none()


def create_consent(
    db: Session,
    *,
    user_id: uuid.UUID,
    template_id: str,
    template_version: str,
) -> WorkflowConsent:
    consent = WorkflowConsent(
        user_id=user_id,
        template_id=template_id,
        template_version=template_version,
    )
    db.add(consent)
    db.flush()
    return consent


def list_consents(db: Session, *, user_id: uuid.UUID) -> list[WorkflowConsent]:
    statement = (
        select(WorkflowConsent)
        .where(WorkflowConsent.user_id == user_id)
        .order_by(WorkflowConsent.consented_at.desc())
    )
    return list(db.execute(statement).scalars().all())
