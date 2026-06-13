from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.model_router import ModelRouterRequest, ModelRouterResponse
from app.services import model_router_service


router = APIRouter(prefix="/model-router", tags=["model-router"])


@router.post("/stub-test", response_model=ModelRouterResponse, status_code=status.HTTP_200_OK)
def model_router_stub_test(
    payload: ModelRouterRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return model_router_service.run_model_stub(
        db,
        owner_id=current_user.id,
        payload=payload,
    )
