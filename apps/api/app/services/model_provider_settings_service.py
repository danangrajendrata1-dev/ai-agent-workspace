import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.provider_settings import (
    SUPPORTED_MODEL_PROVIDER_IDS,
    derive_connection_status,
    normalize_optional_text,
)
from app.repositories import model_provider_setting_repository
from app.schemas.model_provider_setting import (
    ModelProviderSettingsResponse,
    ModelProviderSettingsUpdate,
)


def serialize_settings(setting) -> ModelProviderSettingsResponse:
    return ModelProviderSettingsResponse(
        id=setting.id,
        owner_id=setting.owner_id,
        preferred_provider=setting.preferred_provider,
        preferred_model=setting.preferred_model,
        connection_status=setting.connection_status,
        created_at=setting.created_at,
        updated_at=setting.updated_at,
    )


def get_settings(db: Session, owner_id: uuid.UUID) -> ModelProviderSettingsResponse:
    setting = model_provider_setting_repository.get_by_owner_id(db, owner_id)
    if setting is None:
        setting = model_provider_setting_repository.create_default(db, owner_id)
    return serialize_settings(setting)


def update_settings(
    db: Session,
    owner_id: uuid.UUID,
    payload: ModelProviderSettingsUpdate,
) -> ModelProviderSettingsResponse:
    setting = model_provider_setting_repository.get_by_owner_id(db, owner_id)
    if setting is None:
        setting = model_provider_setting_repository.create_default(db, owner_id)

    update_data = payload.model_dump(exclude_unset=True)
    preferred_provider = update_data.get("preferred_provider", setting.preferred_provider)
    preferred_model = normalize_optional_text(
        update_data.get("preferred_model", setting.preferred_model)
    )

    if preferred_provider is not None and preferred_provider not in SUPPORTED_MODEL_PROVIDER_IDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported model provider.",
        )

    connection_status = derive_connection_status(
        preferred_provider=preferred_provider,
        preferred_model=preferred_model,
    )

    setting = model_provider_setting_repository.update(
        db,
        setting,
        {
            "preferred_provider": preferred_provider,
            "preferred_model": preferred_model,
            "connection_status": connection_status,
        },
    )
    return serialize_settings(setting)
