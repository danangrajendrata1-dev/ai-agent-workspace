import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_n8n_access
from app.schemas.n8n_workflow import (
    N8nWorkflowCreate,
    N8nWorkflowListResponse,
    N8nWorkflowResponse,
    N8nWorkflowUpdate,
)
from app.services import n8n_workflow_service


router = APIRouter(tags=["n8n-workflows"])


@router.post("/n8n-workflows", response_model=N8nWorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    payload: N8nWorkflowCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_n8n_access),
):
    return n8n_workflow_service.create_workflow(db, owner_id=current_user.id, payload=payload)


@router.get("/n8n-workflows", response_model=N8nWorkflowListResponse)
def list_workflows(db: Session = Depends(get_db), current_user=Depends(require_n8n_access)):
    return N8nWorkflowListResponse(items=n8n_workflow_service.list_workflows(db, owner_id=current_user.id))


@router.get("/n8n-workflows/{workflow_id}", response_model=N8nWorkflowResponse)
def get_workflow(
    workflow_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_n8n_access),
):
    return n8n_workflow_service.get_workflow(db, owner_id=current_user.id, workflow_id=workflow_id)


@router.patch("/n8n-workflows/{workflow_id}", response_model=N8nWorkflowResponse)
def update_workflow(
    workflow_id: uuid.UUID,
    payload: N8nWorkflowUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_n8n_access),
):
    return n8n_workflow_service.update_workflow(
        db,
        owner_id=current_user.id,
        workflow_id=workflow_id,
        payload=payload,
    )


@router.delete("/n8n-workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(
    workflow_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_n8n_access),
):
    n8n_workflow_service.delete_workflow(db, owner_id=current_user.id, workflow_id=workflow_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
