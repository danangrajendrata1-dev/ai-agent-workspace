from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.model_provider_api_key import (
    ModelProviderApiKeyDeleteResponse,
    ModelProviderApiKeyListResponse,
    ModelProviderApiKeySaveRequest,
    ModelProviderApiKeyStatusResponse,
)
from app.services import model_provider_api_key_service


router = APIRouter(prefix="/model-provider-keys", tags=["model-provider-keys"])


@router.get("", response_model=ModelProviderApiKeyListResponse)
def list_model_provider_keys(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return model_provider_api_key_service.list_provider_api_key_statuses(db, owner_id=current_user.id)


@router.get("/{provider}", response_model=ModelProviderApiKeyStatusResponse)
def get_model_provider_key(
    provider: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return model_provider_api_key_service.get_provider_api_key_status(
        db,
        owner_id=current_user.id,
        provider=provider,
    )


@router.put("/{provider}", response_model=ModelProviderApiKeyStatusResponse, status_code=status.HTTP_200_OK)
def save_model_provider_key(
    provider: str,
    payload: ModelProviderApiKeySaveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return model_provider_api_key_service.save_provider_api_key(
        db,
        owner_id=current_user.id,
        provider=provider,
        payload=payload,
    )


@router.delete("/{provider}", response_model=ModelProviderApiKeyDeleteResponse, status_code=status.HTTP_200_OK)
def delete_model_provider_key(
    provider: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return model_provider_api_key_service.delete_provider_api_key(
        db,
        owner_id=current_user.id,
        provider=provider,
    )
