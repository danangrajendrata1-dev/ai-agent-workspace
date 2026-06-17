from fastapi import APIRouter, Depends

from app.core.dependencies import require_owner
from app.schemas.runtime import RuntimeCapabilityListResponse
from app.services import runtime_capability_service


router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/capabilities", response_model=RuntimeCapabilityListResponse)
def list_runtime_capabilities(_: object = Depends(require_owner)):
    return RuntimeCapabilityListResponse(items=runtime_capability_service.list_runtime_capabilities())
