import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.workflow import (
    WorkflowConsentListResponse,
    WorkflowConsentResponse,
    WorkflowExecutionListResponse,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowSkillBindingListResponse,
    WorkflowSkillBindingRequest,
    WorkflowSkillBindingResponse,
    WorkflowTemplateListResponse,
)
from app.services import workflow_service


router = APIRouter(tags=["workflows"])


@router.get("/workflows/templates", response_model=WorkflowTemplateListResponse)
def list_workflow_templates(
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return WorkflowTemplateListResponse(
        items=workflow_service.list_workflow_templates_for_user(db, user=current_user)
    )


@router.post("/workflows/consent/{template_id}", response_model=WorkflowConsentResponse, status_code=status.HTTP_201_CREATED)
def create_workflow_consent(
    template_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return workflow_service.create_workflow_consent(db, user=current_user, template_id=template_id)


@router.get("/workflows/consents", response_model=WorkflowConsentListResponse)
def list_workflow_consents(
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return WorkflowConsentListResponse(items=workflow_service.list_workflow_consents(db, user=current_user))


@router.post("/workflows/bindings", response_model=WorkflowSkillBindingResponse, status_code=status.HTTP_201_CREATED)
def create_workflow_binding(
    payload: WorkflowSkillBindingRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    try:
        skill_id = uuid.UUID(payload.skill_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid skill_id.",
        )
    return workflow_service.create_workflow_skill_binding(
        db,
        user=current_user,
        skill_id=skill_id,
        template_id=payload.template_id,
    )


@router.get("/workflows/bindings", response_model=WorkflowSkillBindingListResponse)
def list_workflow_bindings(
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return WorkflowSkillBindingListResponse(
        items=workflow_service.list_workflow_skill_bindings(db, user=current_user)
    )


@router.delete("/workflows/bindings/{binding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow_binding(
    binding_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    workflow_service.delete_workflow_skill_binding(db, user=current_user, binding_id=binding_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/workflows/executions", response_model=WorkflowExecutionListResponse)
def list_workflow_executions(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return WorkflowExecutionListResponse(
        items=workflow_service.list_workflow_executions(
            db,
            user=current_user,
            limit=limit,
            offset=offset,
        )
    )


@router.post("/workflows/execute/{template_id}", response_model=WorkflowExecutionResponse)
def execute_workflow_template(
    template_id: str,
    payload: WorkflowExecutionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    result = workflow_service.execute_workflow_template(
        db,
        user=current_user,
        template_id=template_id,
        request=payload,
    )
    if result.status == "consent_required":
        return JSONResponse(status_code=status.HTTP_428_PRECONDITION_REQUIRED, content=result.model_dump(mode="json"))
    return result
