from fastapi import APIRouter, Depends

from app.core.dependencies import require_owner
from app.schemas.runtime import (
    RuntimeCapabilityListResponse,
    RuntimeEventContractResponse,
    RuntimeReadinessResponse,
)
from app.services import runtime_capability_service, runtime_event_contract_service, runtime_readiness_service


router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/capabilities", response_model=RuntimeCapabilityListResponse)
def list_runtime_capabilities(_: object = Depends(require_owner)):
    return RuntimeCapabilityListResponse(items=runtime_capability_service.list_runtime_capabilities())


@router.get("/readiness", response_model=RuntimeReadinessResponse)
def get_runtime_readiness(_: object = Depends(require_owner)):
    return runtime_readiness_service.get_runtime_readiness()


@router.get("/event-contract", response_model=RuntimeEventContractResponse)
def get_runtime_event_contract(_: object = Depends(require_owner)):
    return runtime_event_contract_service.get_runtime_event_contract()
