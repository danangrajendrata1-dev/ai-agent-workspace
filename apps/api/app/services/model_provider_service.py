import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import model_provider_repository
from app.schemas.model_provider import (
    ModelProviderCreate,
    ModelProviderResponse,
    ModelProviderUpdate,
)


def mask_secret_reference(secret_reference: str | None) -> tuple[bool, str | None]:
    if not secret_reference:
        return False, None
    if len(secret_reference) <= 4:
        return True, "*" * len(secret_reference)
    return True, f"{secret_reference[:2]}{'*' * (len(secret_reference) - 4)}{secret_reference[-2:]}"


def validate_provider_config(
    db: Session,
    *,
    payload: dict,
    provider_id: uuid.UUID | None = None,
) -> None:
    provider_type = payload.get("provider_type")
    auth_type = payload.get("auth_type")
    is_private = payload.get("is_private")
    fallback_provider_id = payload.get("fallback_provider_id")

    if provider_type == "subscription_oauth" and auth_type == "oauth_gateway" and is_private is not True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription OAuth providers must remain private.",
        )

    if fallback_provider_id is not None:
        if provider_id is not None and fallback_provider_id == provider_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fallback provider cannot reference itself.",
            )

        fallback_provider = model_provider_repository.get_active_by_id(db, fallback_provider_id)
        if fallback_provider is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fallback provider must reference an active provider.",
            )


def serialize_provider(provider) -> ModelProviderResponse:
    has_secret_reference, masked_secret_reference = mask_secret_reference(
        provider.secret_reference
    )
    return ModelProviderResponse(
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type,
        base_url=provider.base_url,
        auth_type=provider.auth_type,
        default_model=provider.default_model,
        fallback_provider_id=provider.fallback_provider_id,
        status=provider.status,
        is_private=provider.is_private,
        has_secret_reference=has_secret_reference,
        masked_secret_reference=masked_secret_reference,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


def create_provider(db: Session, payload: ModelProviderCreate) -> ModelProviderResponse:
    provider_data = payload.model_dump()
    validate_provider_config(db, payload=provider_data)
    provider = model_provider_repository.create(db, provider_data)
    return serialize_provider(provider)


def list_providers(db: Session) -> list[ModelProviderResponse]:
    providers = model_provider_repository.list(db)
    return [serialize_provider(provider) for provider in providers]


def get_provider(db: Session, provider_id: uuid.UUID) -> ModelProviderResponse:
    provider = model_provider_repository.get_by_id(db, provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model provider not found.",
        )
    return serialize_provider(provider)


def update_provider(
    db: Session,
    provider_id: uuid.UUID,
    payload: ModelProviderUpdate,
) -> ModelProviderResponse:
    provider = model_provider_repository.get_by_id(db, provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model provider not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    candidate = {
        "provider_type": update_data.get("provider_type", provider.provider_type),
        "auth_type": update_data.get("auth_type", provider.auth_type),
        "is_private": update_data.get("is_private", provider.is_private),
        "fallback_provider_id": update_data.get(
            "fallback_provider_id", provider.fallback_provider_id
        ),
    }
    validate_provider_config(db, payload=candidate, provider_id=provider_id)

    provider = model_provider_repository.update(db, provider, update_data)
    return serialize_provider(provider)


def deactivate_provider(db: Session, provider_id: uuid.UUID) -> ModelProviderResponse:
    provider = model_provider_repository.get_by_id(db, provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model provider not found.",
        )
    provider = model_provider_repository.deactivate(db, provider)
    return serialize_provider(provider)
