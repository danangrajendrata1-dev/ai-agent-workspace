import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.model_provider import ModelProvider


def create(db: Session, provider_data: dict) -> ModelProvider:
    provider = ModelProvider(**provider_data)
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


def get_by_id(db: Session, provider_id: uuid.UUID) -> ModelProvider | None:
    statement = select(ModelProvider).where(ModelProvider.id == provider_id)
    return db.execute(statement).scalar_one_or_none()


def list(db: Session) -> list[ModelProvider]:
    statement = select(ModelProvider).order_by(ModelProvider.created_at.desc())
    return db.execute(statement).scalars().all()


def update(db: Session, provider: ModelProvider, provider_data: dict) -> ModelProvider:
    for field, value in provider_data.items():
        setattr(provider, field, value)
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


def deactivate(db: Session, provider: ModelProvider) -> ModelProvider:
    provider.status = "inactive"
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


def get_active_by_id(db: Session, provider_id: uuid.UUID) -> ModelProvider | None:
    statement = select(ModelProvider).where(
        ModelProvider.id == provider_id,
        ModelProvider.status == "active",
    )
    return db.execute(statement).scalar_one_or_none()
