from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.tool_execution import ToolExecutionRequest, ToolExecutionResponse
from app.services import tool_execution_service


router = APIRouter(tags=["tool-execution"])


@router.post(
    "/tools/execution-stub",
    response_model=ToolExecutionResponse,
    status_code=status.HTTP_200_OK,
)
def request_tool_execution_stub(
    payload: ToolExecutionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return tool_execution_service.request_tool_execution_stub(
        db,
        owner_id=current_user.id,
        payload=payload,
    )
