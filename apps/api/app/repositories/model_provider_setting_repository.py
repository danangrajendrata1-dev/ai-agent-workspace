import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.provider_settings import CONNECTION_STATUS_NOT_CONNECTED
from app.models.model_provider_setting import ModelProviderSetting


def get_by_owner_id(db: Session, owner_id: uuid.UUID) -> ModelProviderSetting | None:
    statement = select(ModelProviderSetting).where(ModelProviderSetting.owner_id == owner_id)
    return db.execute(statement).scalar_one_or_none()


def create_default(db: Session, owner_id: uuid.UUID) -> ModelProviderSetting:
    setting = ModelProviderSetting(
        owner_id=owner_id,
        preferred_provider=None,
        preferred_model=None,
        connection_status=CONNECTION_STATUS_NOT_CONNECTED,
    )
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def update(db: Session, setting: ModelProviderSetting, update_data: dict) -> ModelProviderSetting:
    for field, value in update_data.items():
        setattr(setting, field, value)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting
