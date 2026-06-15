import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.provider_api_keys import (
    API_KEY_CONNECTION_STATUS_CONNECTED,
    API_KEY_CONNECTION_STATUS_NOT_CONNECTED,
    encrypt_api_key,
    get_api_key_last4,
    mask_api_key,
    normalize_api_key,
    SUPPORTED_API_KEY_PROVIDER_IDS,
    validate_api_key_provider,
)
from app.repositories import model_provider_api_key_repository
from app.schemas.model_provider_api_key import (
    ModelProviderApiKeyListResponse,
    ModelProviderApiKeySaveRequest,
    ModelProviderApiKeyStatusResponse,
)
from app.services import log_service


MASKED_PREFIX = "********"


def serialize_api_key(record, *, provider: str) -> ModelProviderApiKeyStatusResponse:
    if record is None:
        return ModelProviderApiKeyStatusResponse(
            id=None,
            owner_id=None,
            provider=provider,
            connection_status=API_KEY_CONNECTION_STATUS_NOT_CONNECTED,
            masked_key=None,
            key_last4=None,
            created_at=None,
            updated_at=None,
        )

    masked_key = mask_api_key(record.key_last4)
    if masked_key is None:
        masked_key = f"{record.key_prefix_masked}{record.key_last4}"

    return ModelProviderApiKeyStatusResponse(
        id=record.id,
        owner_id=record.owner_id,
        provider=record.provider,
        connection_status=record.connection_status,
        masked_key=masked_key,
        key_last4=record.key_last4,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def get_provider_api_key_status(
    db: Session,
    *,
    owner_id: uuid.UUID,
    provider: str,
) -> ModelProviderApiKeyStatusResponse:
    normalized_provider = validate_api_key_provider(provider)
    record = model_provider_api_key_repository.get_by_owner_and_provider(
        db,
        owner_id,
        normalized_provider,
    )
    return serialize_api_key(record, provider=normalized_provider)


def list_provider_api_key_statuses(
    db: Session,
    *,
    owner_id: uuid.UUID,
) -> ModelProviderApiKeyListResponse:
    records = {
        record.provider: record
        for record in model_provider_api_key_repository.list_by_owner(db, owner_id)
    }
    items = [
        serialize_api_key(records.get(provider), provider=provider)
        for provider in SUPPORTED_API_KEY_PROVIDER_IDS
    ]
    return ModelProviderApiKeyListResponse(items=items)


def save_provider_api_key(
    db: Session,
    *,
    owner_id: uuid.UUID,
    provider: str,
    payload: ModelProviderApiKeySaveRequest,
) -> ModelProviderApiKeyStatusResponse:
    normalized_provider = validate_api_key_provider(provider)
    api_key = normalize_api_key(payload.api_key)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key is required.",
        )
    encrypted_api_key = encrypt_api_key(api_key)
    key_last4 = get_api_key_last4(api_key)
    record = model_provider_api_key_repository.get_by_owner_and_provider(
        db,
        owner_id,
        normalized_provider,
    )

    if record is None:
        record = model_provider_api_key_repository.create(
            db,
            owner_id=owner_id,
            provider=normalized_provider,
            encrypted_api_key=encrypted_api_key,
            key_last4=key_last4,
            key_prefix_masked=MASKED_PREFIX,
            connection_status=API_KEY_CONNECTION_STATUS_CONNECTED,
        )
    else:
        record = model_provider_api_key_repository.update(
            db,
            record,
            encrypted_api_key=encrypted_api_key,
            key_last4=key_last4,
            key_prefix_masked=MASKED_PREFIX,
            connection_status=API_KEY_CONNECTION_STATUS_CONNECTED,
        )

    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=owner_id,
        request_id=None,
        event_type="model_provider_api_key.saved",
        message="Model provider API key saved.",
        metadata_json={
            "provider": normalized_provider,
            "key_last4": key_last4,
            "connection_status": API_KEY_CONNECTION_STATUS_CONNECTED,
        },
    )
    db.commit()
    return serialize_api_key(record, provider=normalized_provider)


def delete_provider_api_key(
    db: Session,
    *,
    owner_id: uuid.UUID,
    provider: str,
) -> ModelProviderApiKeyStatusResponse:
    normalized_provider = validate_api_key_provider(provider)
    record = model_provider_api_key_repository.get_by_owner_and_provider(
        db,
        owner_id,
        normalized_provider,
    )
    if record is None:
        return serialize_api_key(None, provider=normalized_provider)

    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=owner_id,
        request_id=None,
        event_type="model_provider_api_key.deleted",
        message="Model provider API key deleted.",
        metadata_json={
            "provider": normalized_provider,
            "key_last4": record.key_last4,
            "connection_status": API_KEY_CONNECTION_STATUS_NOT_CONNECTED,
        },
    )
    model_provider_api_key_repository.delete(db, record)
    db.commit()
    return serialize_api_key(None, provider=normalized_provider)
