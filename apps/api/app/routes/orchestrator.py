from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.orchestrator import OrchestratorRequest, OrchestratorResponse
from app.services import orchestrator_service


router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.post("/chat", response_model=OrchestratorResponse)
def chat_workspace(
    payload: OrchestratorRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return orchestrator_service.orchestrate_workspace_chat(
        db,
        owner_id=current_user.id,
        payload=payload,
        current_user=current_user,
    )
