from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.model_provider_setting import (
    ModelProviderSettingsResponse,
    ModelProviderSettingsUpdate,
)
from app.services import model_provider_settings_service


router = APIRouter(prefix="/model-provider-settings", tags=["model-provider-settings"])


@router.get("", response_model=ModelProviderSettingsResponse)
def get_model_provider_settings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return model_provider_settings_service.get_settings(db, owner_id=current_user.id)


@router.patch("", response_model=ModelProviderSettingsResponse, status_code=status.HTTP_200_OK)
def update_model_provider_settings(
    payload: ModelProviderSettingsUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return model_provider_settings_service.update_settings(db, owner_id=current_user.id, payload=payload)
