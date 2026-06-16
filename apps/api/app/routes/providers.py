from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.model_provider_api_key import ProviderTestRequest, ProviderTestResponse
from app.services import provider_test_service


router = APIRouter(prefix="/providers", tags=["providers"])


@router.post("/test-connection", response_model=ProviderTestResponse)
def test_provider_connection(
    payload: ProviderTestRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return provider_test_service.test_provider_connection(
        db,
        owner_id=current_user.id,
        provider=payload.provider,
    )
