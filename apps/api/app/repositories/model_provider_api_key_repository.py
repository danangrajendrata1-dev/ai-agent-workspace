import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.model_provider_api_key import ModelProviderApiKey


def get_by_owner_and_provider(db: Session, owner_id: uuid.UUID, provider: str) -> ModelProviderApiKey | None:
    statement = select(ModelProviderApiKey).where(
        ModelProviderApiKey.owner_id == owner_id,
        ModelProviderApiKey.provider == provider,
    )
    return db.execute(statement).scalar_one_or_none()


def list_by_owner(db: Session, owner_id: uuid.UUID) -> list[ModelProviderApiKey]:
    statement = select(ModelProviderApiKey).where(
        ModelProviderApiKey.owner_id == owner_id,
    )
    return db.execute(statement).scalars().all()


def create(
    db: Session,
    *,
    owner_id: uuid.UUID,
    provider: str,
    encrypted_api_key: str,
    key_last4: str,
    key_prefix_masked: str,
    connection_status: str,
) -> ModelProviderApiKey:
    record = ModelProviderApiKey(
        owner_id=owner_id,
        provider=provider,
        encrypted_api_key=encrypted_api_key,
        key_last4=key_last4,
        key_prefix_masked=key_prefix_masked,
        connection_status=connection_status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update(
    db: Session,
    record: ModelProviderApiKey,
    *,
    encrypted_api_key: str,
    key_last4: str,
    key_prefix_masked: str,
    connection_status: str,
) -> ModelProviderApiKey:
    record.encrypted_api_key = encrypted_api_key
    record.key_last4 = key_last4
    record.key_prefix_masked = key_prefix_masked
    record.connection_status = connection_status
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def delete(db: Session, record: ModelProviderApiKey) -> None:
    db.delete(record)
    db.commit()
