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
        WorkflowConsent.revoked_at.is_(None),
    )
    return db.execute(statement).scalar_one_or_none()


def get_consent_any_status(
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


def get_consent_by_id(
    db: Session,
    *,
    user_id: uuid.UUID,
    consent_id: uuid.UUID,
) -> WorkflowConsent | None:
    statement = select(WorkflowConsent).where(
        WorkflowConsent.user_id == user_id,
        WorkflowConsent.id == consent_id,
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


def list_consents(
    db: Session,
    *,
    user_id: uuid.UUID,
    limit: int | None = None,
    offset: int = 0,
) -> list[WorkflowConsent]:
    statement = select(WorkflowConsent).where(WorkflowConsent.user_id == user_id).order_by(
        WorkflowConsent.consented_at.desc(),
        WorkflowConsent.id.desc(),
    )
    if offset > 0:
        statement = statement.offset(offset)
    if limit is not None:
        statement = statement.limit(max(limit, 1))
    return list(db.execute(statement).scalars().all())
