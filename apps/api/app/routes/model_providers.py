import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.model_provider import (
    ModelProviderCreate,
    ModelProviderListResponse,
    ModelProviderResponse,
    ModelProviderUpdate,
)
from app.services import model_provider_service


router = APIRouter(
    prefix="/model-providers",
    tags=["model-providers"],
    dependencies=[Depends(require_owner)],
)


@router.post("", response_model=ModelProviderResponse, status_code=status.HTTP_201_CREATED)
def create_model_provider(payload: ModelProviderCreate, db: Session = Depends(get_db)):
    return model_provider_service.create_provider(db, payload)


@router.get("", response_model=ModelProviderListResponse)
def list_model_providers(db: Session = Depends(get_db)):
    return ModelProviderListResponse(items=model_provider_service.list_providers(db))


@router.get("/{provider_id}", response_model=ModelProviderResponse)
def get_model_provider(provider_id: uuid.UUID, db: Session = Depends(get_db)):
    return model_provider_service.get_provider(db, provider_id)


@router.patch("/{provider_id}", response_model=ModelProviderResponse)
def update_model_provider(
    provider_id: uuid.UUID,
    payload: ModelProviderUpdate,
    db: Session = Depends(get_db),
):
    return model_provider_service.update_provider(db, provider_id, payload)


@router.post("/{provider_id}/deactivate", response_model=ModelProviderResponse)
def deactivate_model_provider(provider_id: uuid.UUID, db: Session = Depends(get_db)):
    return model_provider_service.deactivate_provider(db, provider_id)
