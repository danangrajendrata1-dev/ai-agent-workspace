import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import n8n_workflow_repository
from app.schemas.n8n_workflow import N8nWorkflowCreate, N8nWorkflowResponse, N8nWorkflowUpdate
from app.services import log_service


BLOCKED_SECRET_PATTERNS = [
    r"(?i)\bsk-[A-Za-z0-9_\-]+\b",
    r"(?i)\bapi[_-]?key\b",
    r"(?i)\bsecret\b",
    r"(?i)\btoken\b",
    r"(?i)\bbearer\b",
    r"(?i)\bpassword\b",
]
BLOCKED_WEBHOOK_PATTERNS = [
    r"(?i)https?://",
    r"(?i)[?&](token|secret|api_key|key)=",
]


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:180] or "n8n-workflow"


def ensure_unique_slug(
    db: Session,
    *,
    slug: str,
    current_workflow_id: uuid.UUID | None = None,
) -> str:
    existing = n8n_workflow_repository.get_by_slug(db, slug)
    if existing is None or existing.id == current_workflow_id:
        return slug
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Workflow slug is already in use.",
    )


def _contains_secret_like_value(value) -> bool:
    if isinstance(value, dict):
        return any(_contains_secret_like_value(key) or _contains_secret_like_value(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_secret_like_value(item) for item in value)
    if isinstance(value, str):
        return any(re.search(pattern, value) for pattern in BLOCKED_SECRET_PATTERNS + BLOCKED_WEBHOOK_PATTERNS)
    return False


def validate_no_plaintext_secret(
    webhook_url_reference: str | None,
    metadata: dict | None,
) -> None:
    if webhook_url_reference:
        if any(re.search(pattern, webhook_url_reference) for pattern in BLOCKED_SECRET_PATTERNS + BLOCKED_WEBHOOK_PATTERNS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook reference must be a safe label, not a raw URL or secret-like value.",
            )

    if metadata is not None and _contains_secret_like_value(metadata):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow metadata contains secret-like values and cannot be stored.",
        )


def enforce_risk_rules(workflow_data: dict) -> dict:
    normalized = dict(workflow_data)
    risk_level = normalized.get("risk_level")

    if risk_level == "high":
        normalized["approval_required"] = True

    if risk_level == "critical":
        normalized["approval_required"] = True
        normalized["status"] = "disabled"

    return normalized


def serialize_workflow(workflow) -> N8nWorkflowResponse:
    return N8nWorkflowResponse(
        id=workflow.id,
        owner_id=workflow.owner_id,
        name=workflow.name,
        slug=workflow.slug,
        description=workflow.description,
        workflow_external_id=workflow.workflow_external_id,
        trigger_type=workflow.trigger_type,
        webhook_url_reference=workflow.webhook_url_reference,
        status=workflow.status,
        risk_level=workflow.risk_level,
        approval_required=workflow.approval_required,
        metadata=workflow.metadata_json,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        deleted_at=workflow.deleted_at,
    )


def create_workflow(db: Session, *, owner_id: uuid.UUID, payload: N8nWorkflowCreate) -> N8nWorkflowResponse:
    validate_no_plaintext_secret(payload.webhook_url_reference, payload.metadata)

    workflow_data = enforce_risk_rules(payload.model_dump())
    workflow_data["owner_id"] = owner_id
    workflow_data["slug"] = ensure_unique_slug(db, slug=normalize_slug(payload.slug or payload.name))
    workflow_data["metadata_json"] = workflow_data.pop("metadata", None)

    workflow = n8n_workflow_repository.create(db, workflow_data)
    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=owner_id,
        request_id=None,
        event_type="n8n_workflow.created",
        message="n8n workflow registry item created.",
        metadata_json={"workflow_id": str(workflow.id), "risk_level": workflow.risk_level},
    )
    db.commit()
    db.refresh(workflow)
    return serialize_workflow(workflow)


def list_workflows(db: Session, *, owner_id: uuid.UUID) -> list[N8nWorkflowResponse]:
    workflows = n8n_workflow_repository.list_by_owner(db, owner_id)
    return [serialize_workflow(workflow) for workflow in workflows]


def get_workflow(db: Session, *, owner_id: uuid.UUID, workflow_id: uuid.UUID) -> N8nWorkflowResponse:
    workflow = n8n_workflow_repository.get_by_id(db, owner_id, workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="n8n workflow not found.",
        )
    return serialize_workflow(workflow)


def update_workflow(
    db: Session,
    *,
    owner_id: uuid.UUID,
    workflow_id: uuid.UUID,
    payload: N8nWorkflowUpdate,
) -> N8nWorkflowResponse:
    workflow = n8n_workflow_repository.get_by_id(db, owner_id, workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="n8n workflow not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    candidate = {
        "name": update_data.get("name", workflow.name),
        "slug": update_data.get("slug", workflow.slug),
        "description": update_data.get("description", workflow.description),
        "workflow_external_id": update_data.get("workflow_external_id", workflow.workflow_external_id),
        "trigger_type": update_data.get("trigger_type", workflow.trigger_type),
        "webhook_url_reference": update_data.get("webhook_url_reference", workflow.webhook_url_reference),
        "status": update_data.get("status", workflow.status),
        "risk_level": update_data.get("risk_level", workflow.risk_level),
        "approval_required": update_data.get("approval_required", workflow.approval_required),
        "metadata": update_data.get("metadata", workflow.metadata_json),
    }
    validate_no_plaintext_secret(candidate["webhook_url_reference"], candidate["metadata"])
    candidate = enforce_risk_rules(candidate)

    if "slug" in update_data or "name" in update_data:
        source_slug = update_data.get("slug") or update_data.get("name") or workflow.slug
        candidate["slug"] = ensure_unique_slug(
            db,
            slug=normalize_slug(source_slug),
            current_workflow_id=workflow.id,
        )

    candidate["metadata_json"] = candidate.pop("metadata", None)

    workflow = n8n_workflow_repository.update(db, workflow, candidate)
    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=owner_id,
        request_id=None,
        event_type="n8n_workflow.updated",
        message="n8n workflow registry item updated.",
        metadata_json={"workflow_id": str(workflow.id), "risk_level": workflow.risk_level},
    )
    db.commit()
    db.refresh(workflow)
    return serialize_workflow(workflow)


def delete_workflow(db: Session, *, owner_id: uuid.UUID, workflow_id: uuid.UUID) -> None:
    workflow = n8n_workflow_repository.get_by_id(db, owner_id, workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="n8n workflow not found.",
        )

    n8n_workflow_repository.soft_delete(db, workflow, datetime.now(UTC))
    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=owner_id,
        request_id=None,
        event_type="n8n_workflow.deleted",
        message="n8n workflow registry item soft-deleted.",
        metadata_json={"workflow_id": str(workflow.id)},
    )
    db.commit()
