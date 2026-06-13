import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.tool import (
    AgentToolAssignRequest,
    AgentToolResponse,
    ToolCreate,
    ToolListResponse,
    ToolResponse,
    ToolUpdate,
)
from app.services import tool_service


router = APIRouter(tags=["tools"])


@router.post("/tools", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
def create_tool(
    payload: ToolCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return tool_service.create_tool(db, payload)


@router.get("/tools", response_model=ToolListResponse)
def list_tools(db: Session = Depends(get_db), current_user=Depends(require_owner)):
    return ToolListResponse(items=tool_service.list_tools(db))


@router.get("/tools/{tool_id}", response_model=ToolResponse)
def get_tool(
    tool_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return tool_service.get_tool(db, tool_id)


@router.patch("/tools/{tool_id}", response_model=ToolResponse)
def update_tool(
    tool_id: uuid.UUID,
    payload: ToolUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return tool_service.update_tool(db, tool_id, payload)


@router.post("/tools/{tool_id}/deactivate", response_model=ToolResponse)
def deactivate_tool(
    tool_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return tool_service.deactivate_tool(db, tool_id)


@router.post(
    "/agents/{agent_id}/tools",
    response_model=AgentToolResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_tool_to_agent(
    agent_id: uuid.UUID,
    payload: AgentToolAssignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return tool_service.assign_tool_to_agent(
        db,
        owner_id=current_user.id,
        agent_id=agent_id,
        payload=payload,
    )


@router.get("/agents/{agent_id}/tools", response_model=list[AgentToolResponse])
def list_agent_tools(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return tool_service.list_agent_tools(db, owner_id=current_user.id, agent_id=agent_id)


@router.delete("/agents/{agent_id}/tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tool_from_agent(
    agent_id: uuid.UUID,
    tool_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    tool_service.remove_tool_from_agent(
        db,
        owner_id=current_user.id,
        agent_id=agent_id,
        tool_id=tool_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
