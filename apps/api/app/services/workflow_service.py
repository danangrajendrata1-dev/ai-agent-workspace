from __future__ import annotations

import threading
import time
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.workflow_webhook_client import WebhookCallResult, call_template_webhook
from app.core.subscription_plans import is_admin_role
from app.core.webhook_security import (
    canonicalize_webhook_url,
    sanitize_error_message,
    sanitize_payload_for_template,
    validate_safe_webhook_url,
)
from app.core.workflow_templates import get_workflow_template, get_workflow_templates
from app.repositories import (
    agent_repository,
    skill_repository,
    workflow_consent_repository,
    workflow_execution_repository,
    workflow_skill_binding_repository,
)
from app.schemas.workflow import (
    WorkflowChatExecutionRequest,
    WorkflowConsentResponse,
    WorkflowExecutionHistoryItem,
    WorkflowExecutionHistoryListResponse,
    WorkflowExecutionSummary,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowSkillBindingResponse,
    WorkflowTemplateResponse,
)
from app.services import log_service, skill_service


WORKFLOW_CONSENT_RATE_LIMIT_MAX_REQUESTS = 10
WORKFLOW_BINDING_RATE_LIMIT_MAX_REQUESTS = 10
WORKFLOW_LIST_RATE_LIMIT_MAX_REQUESTS = 20
WORKFLOW_EXECUTE_RATE_LIMIT_MAX_REQUESTS = 5
WORKFLOW_RATE_LIMIT_WINDOW_SECONDS = 60

_rate_limit_lock = threading.Lock()
_rate_limit_state: dict[str, list[float]] = {}


def clear_workflow_rate_limiter() -> None:
    with _rate_limit_lock:
        _rate_limit_state.clear()


def _safe_record_activity(record_fn, db: Session, **kwargs) -> None:
    try:
        record_fn(db, **kwargs)
    except Exception:
        db.rollback()


def _rate_limit_bucket(owner_id: uuid.UUID, action: str, max_requests: int) -> list[float]:
    now = time.monotonic()
    key = f"{owner_id}:{action}"
    with _rate_limit_lock:
        bucket = _rate_limit_state.setdefault(key, [])
        bucket[:] = [timestamp for timestamp in bucket if now - timestamp < WORKFLOW_RATE_LIMIT_WINDOW_SECONDS]
        if len(bucket) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Terlalu banyak pesan, tunggu sebentar",
            )
        bucket.append(now)
        return bucket


def _require_owner_access(current_user) -> None:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials.")
    if is_admin_role(getattr(current_user, "role", None)):
        return


def _load_workflow_template_or_404(template_id: str) -> dict:
    template = get_workflow_template(template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow template not found.")
    return template


def _ensure_template_enabled(template: dict) -> None:
    if not template.get("enabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow template is disabled.",
        )


def _ensure_template_url_safe(template: dict) -> None:
    is_safe, reason = validate_safe_webhook_url(str(template.get("webhook_url") or ""))
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason or "Workflow template URL is not safe.",
        )


def _serialize_template(template: dict, consent: WorkflowConsentResponse | None = None) -> WorkflowTemplateResponse:
    return WorkflowTemplateResponse(
        id=str(template["id"]),
        name=str(template["name"]),
        description=str(template["description"]),
        input_schema=dict(template.get("input_schema") or {}),
        template_version=str(template["template_version"]),
        risk_level=str(template["risk_level"]),
        output_type=str(template["output_type"]),
        enabled=bool(template["enabled"]),
        max_payload_bytes=int(template["max_payload_bytes"]),
        consented=bool(consent is not None),
        consented_at=getattr(consent, "consented_at", None),
    )


def _serialize_consent(consent) -> WorkflowConsentResponse:
    template = get_workflow_template(str(consent.template_id)) or {"name": consent.template_id}
    return WorkflowConsentResponse(
        id=consent.id,
        user_id=consent.user_id,
        template_id=consent.template_id,
        template_name=str(template.get("name") or consent.template_id),
        template_version=consent.template_version,
        consented_at=consent.consented_at,
        revoked_at=getattr(consent, "revoked_at", None),
        status="revoked" if getattr(consent, "revoked_at", None) is not None else "active",
    )


def _serialize_binding(db: Session, binding) -> WorkflowSkillBindingResponse:
    skill = skill_repository.get_by_id(db, binding.skill_id)
    template = get_workflow_template(str(binding.template_id)) or {"name": binding.template_id}
    skill_name = getattr(skill, "name", None) if skill is not None else None
    return WorkflowSkillBindingResponse(
        id=binding.id,
        user_id=binding.user_id,
        skill_id=binding.skill_id,
        skill_name=skill_name or "Deleted skill",
        skill_type="workflow_skill",
        template_id=binding.template_id,
        template_name=str(template.get("name") or binding.template_id),
        template_version=binding.template_version,
        created_at=binding.created_at,
    )


def _serialize_execution(execution) -> WorkflowExecutionSummary:
    template = get_workflow_template(str(execution.template_id)) or {"name": execution.template_id}
    return WorkflowExecutionSummary(
        id=execution.id,
        user_id=execution.user_id,
        agent_id=execution.agent_id,
        skill_id=execution.skill_id,
        template_id=execution.template_id,
        template_name=str(template.get("name") or execution.template_id),
        template_version=execution.template_version,
        consent_id=execution.consent_id,
        status=execution.status,
        error_message=sanitize_error_message(execution.error_message) if execution.error_message else None,
        http_status_code=execution.http_status_code,
        output_summary=execution.output_summary,
        executed_at=execution.executed_at,
    )


def _serialize_execution_history_item(execution) -> WorkflowExecutionHistoryItem:
    template = get_workflow_template(str(execution.template_id)) or {"name": execution.template_id}
    # Only one timestamp is stored today, so reuse it for both created and completed views.
    timestamp = execution.executed_at
    return WorkflowExecutionHistoryItem(
        id=execution.id,
        template_id=execution.template_id,
        template_name=str(template.get("name") or execution.template_id),
        template_version=execution.template_version,
        agent_id=execution.agent_id,
        skill_id=execution.skill_id,
        status=execution.status,
        error_message=sanitize_error_message(execution.error_message) if execution.error_message else None,
        http_status_code=execution.http_status_code,
        created_at=timestamp,
        completed_at=timestamp,
    )


def _resolve_owned_workflow_skill(db: Session, *, user, skill_id: uuid.UUID):
    owned_agents = agent_repository.list_by_owner(db, user.id)
    for agent in owned_agents:
        active_skills = skill_service.list_active_agent_skills(
            db,
            owner_id=user.id,
            agent_id=agent.id,
            current_user=user,
        )
        for assignment in active_skills:
            if assignment.skill_id == skill_id:
                return assignment
    return None


def _resolve_owned_workflow_skill_for_agent(db: Session, *, user, agent_id: uuid.UUID, skill_id: uuid.UUID):
    active_skills = skill_service.list_active_agent_skills(
        db,
        owner_id=user.id,
        agent_id=agent_id,
        current_user=user,
    )
    for assignment in active_skills:
        if assignment.skill_id == skill_id:
            return assignment
    return None


def _get_skill_type_from_assignment(assignment) -> str | None:
    if isinstance(assignment, dict):
        skill = assignment.get("skill")
    else:
        skill = getattr(assignment, "skill", None)

    if skill is None:
        return None

    if isinstance(skill, dict):
        skill_type = skill.get("type") or skill.get("skill_type")
    else:
        skill_type = getattr(skill, "type", None) or getattr(skill, "skill_type", None)

    if skill_type:
        return str(skill_type)
    return None


def list_workflow_templates_for_user(db: Session, *, user) -> list[WorkflowTemplateResponse]:
    _require_owner_access(user)
    templates = get_workflow_templates(include_disabled=True)
    consents = {
        (consent.template_id, consent.template_version): consent
        for consent in workflow_consent_repository.list_consents(db, user_id=user.id)
        if getattr(consent, "revoked_at", None) is None
    }
    return [
        _serialize_template(
            template,
            consents.get((template["id"], template["template_version"])),
        )
        for template in templates
    ]


def create_workflow_consent(db: Session, *, user, template_id: str) -> WorkflowConsentResponse:
    _require_owner_access(user)
    _rate_limit_bucket(user.id, "consent", WORKFLOW_CONSENT_RATE_LIMIT_MAX_REQUESTS)

    template = _load_workflow_template_or_404(template_id)
    _ensure_template_enabled(template)
    _ensure_template_url_safe(template)

    existing = workflow_consent_repository.get_consent_any_status(
        db,
        user_id=user.id,
        template_id=template_id,
        template_version=str(template["template_version"]),
    )
    if existing is not None:
        if getattr(existing, "revoked_at", None) is not None:
            existing.revoked_at = None
            existing.consented_at = datetime.now(UTC)
            _safe_record_activity(
                log_service.record_activity,
                db,
                actor_type="user",
                actor_id=user.id,
                request_id=None,
                event_type="workflow.consent.reactivated",
                message="Workflow template consent restored.",
                metadata_json={
                    "user_id": str(user.id),
                    "template_id": template_id,
                    "template_version": str(template["template_version"]),
                },
            )
            db.commit()
            db.refresh(existing)
        return _serialize_consent(existing)

    consent = workflow_consent_repository.create_consent(
        db,
        user_id=user.id,
        template_id=template_id,
        template_version=str(template["template_version"]),
    )
    _safe_record_activity(
        log_service.record_activity,
        db,
        actor_type="user",
        actor_id=user.id,
        request_id=None,
        event_type="workflow.consent.created",
        message="Workflow template consent recorded.",
        metadata_json={
            "user_id": str(user.id),
            "template_id": template_id,
            "template_version": str(template["template_version"]),
        },
    )
    db.commit()
    db.refresh(consent)
    return _serialize_consent(consent)


def list_workflow_consents(
    db: Session,
    *,
    user,
    limit: int = 50,
    offset: int = 0,
) -> list[WorkflowConsentResponse]:
    _require_owner_access(user)
    safe_limit = min(max(int(limit), 1), 50)
    safe_offset = max(int(offset), 0)
    consents = workflow_consent_repository.list_consents(
        db,
        user_id=user.id,
        limit=safe_limit,
        offset=safe_offset,
    )
    return [_serialize_consent(consent) for consent in consents]


def revoke_workflow_consent(db: Session, *, user, consent_id: uuid.UUID) -> WorkflowConsentResponse:
    _require_owner_access(user)
    _rate_limit_bucket(user.id, "consent", WORKFLOW_CONSENT_RATE_LIMIT_MAX_REQUESTS)

    consent = workflow_consent_repository.get_consent_by_id(
        db,
        user_id=user.id,
        consent_id=consent_id,
    )
    if consent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow consent not found.",
        )

    if getattr(consent, "revoked_at", None) is None:
        consent.revoked_at = datetime.now(UTC)
        _safe_record_activity(
            log_service.record_activity,
            db,
            actor_type="user",
            actor_id=user.id,
            request_id=None,
            event_type="workflow.consent.revoked",
            message="Workflow template consent revoked.",
            metadata_json={
                "user_id": str(user.id),
                "consent_id": str(consent_id),
                "template_id": consent.template_id,
                "template_version": consent.template_version,
            },
        )
        db.commit()
        db.refresh(consent)

    return _serialize_consent(consent)


def create_workflow_skill_binding(
    db: Session,
    *,
    user,
    skill_id: uuid.UUID,
    template_id: str,
) -> WorkflowSkillBindingResponse:
    _require_owner_access(user)
    _rate_limit_bucket(user.id, "binding", WORKFLOW_BINDING_RATE_LIMIT_MAX_REQUESTS)

    template = _load_workflow_template_or_404(template_id)
    _ensure_template_enabled(template)
    _ensure_template_url_safe(template)

    assignment = _resolve_owned_workflow_skill(db, user=user, skill_id=skill_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow skill not found for the current user.",
        )
    if getattr(assignment.skill, "status", None) != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow skill must be active.",
        )
    if _get_skill_type_from_assignment(assignment) != "workflow_skill":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill must be a workflow_skill.",
        )

    existing = workflow_skill_binding_repository.get_binding(
        db,
        user_id=user.id,
        skill_id=skill_id,
        template_id=template_id,
    )
    if existing is not None and existing.template_version == str(template["template_version"]):
        return _serialize_binding(db, existing)

    binding = workflow_skill_binding_repository.create_binding(
        db,
        user_id=user.id,
        skill_id=skill_id,
        template_id=template_id,
        template_version=str(template["template_version"]),
    )
    _safe_record_activity(
        log_service.record_activity,
        db,
        actor_type="user",
        actor_id=user.id,
        request_id=None,
        event_type="workflow.binding.created",
        message="Workflow skill binding recorded.",
        metadata_json={
            "user_id": str(user.id),
            "skill_id": str(skill_id),
            "template_id": template_id,
            "template_version": str(template["template_version"]),
        },
    )
    db.commit()
    db.refresh(binding)
    return _serialize_binding(db, binding)


def list_workflow_skill_bindings(db: Session, *, user) -> list[WorkflowSkillBindingResponse]:
    _require_owner_access(user)
    bindings = workflow_skill_binding_repository.list_bindings(db, user_id=user.id)
    return [_serialize_binding(db, binding) for binding in bindings]


def delete_workflow_skill_binding(db: Session, *, user, binding_id: uuid.UUID) -> None:
    _require_owner_access(user)
    _rate_limit_bucket(user.id, "binding", WORKFLOW_BINDING_RATE_LIMIT_MAX_REQUESTS)

    binding = workflow_skill_binding_repository.get_binding_by_id(
        db,
        user_id=user.id,
        binding_id=binding_id,
    )
    if binding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow binding not found.",
        )

    workflow_skill_binding_repository.delete_binding(db, binding=binding)
    _safe_record_activity(
        log_service.record_activity,
        db,
        actor_type="user",
        actor_id=user.id,
        request_id=None,
        event_type="workflow.binding.deleted",
        message="Workflow skill binding deleted.",
        metadata_json={
            "user_id": str(user.id),
            "binding_id": str(binding_id),
            "skill_id": str(binding.skill_id),
            "template_id": binding.template_id,
        },
    )
    db.commit()


def list_workflow_executions(
    db: Session,
    *,
    user,
    limit: int = 50,
    offset: int = 0,
) -> list[WorkflowExecutionSummary]:
    _require_owner_access(user)
    _rate_limit_bucket(user.id, "execution_list", WORKFLOW_LIST_RATE_LIMIT_MAX_REQUESTS)
    executions = workflow_execution_repository.list_executions(
        db,
        user_id=user.id,
        limit=limit,
        offset=offset,
    )
    return [_serialize_execution(execution) for execution in executions]


def list_workflow_execution_history(
    db: Session,
    *,
    user,
    limit: int = 25,
    offset: int = 0,
) -> WorkflowExecutionHistoryListResponse:
    _require_owner_access(user)
    safe_limit = min(max(int(limit), 1), 50)
    safe_offset = max(int(offset), 0)
    _rate_limit_bucket(user.id, "execution_history", WORKFLOW_LIST_RATE_LIMIT_MAX_REQUESTS)
    executions = workflow_execution_repository.list_executions(
        db,
        user_id=user.id,
        limit=safe_limit,
        offset=safe_offset,
    )
    return WorkflowExecutionHistoryListResponse(
        items=[_serialize_execution_history_item(execution) for execution in executions]
    )


def _load_agent_for_execution(db: Session, *, user, agent_id: uuid.UUID):
    if is_admin_role(getattr(user, "role", None)):
        agent = agent_repository.get_by_id_for_admin(db, agent_id)
    else:
        agent = agent_repository.get_by_id(db, user.id, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")
    return agent


def _load_owned_workflow_skill_binding(
    db: Session,
    *,
    user,
    agent_id: uuid.UUID,
    skill_id: uuid.UUID,
    template_id: str,
    template_version: str,
):
    binding = workflow_skill_binding_repository.get_binding(
        db,
        user_id=user.id,
        skill_id=skill_id,
        template_id=template_id,
    )
    if binding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow binding not found for the current user.",
        )
    if binding.template_version != template_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow binding version mismatch.",
        )

    assignment = _resolve_owned_workflow_skill_for_agent(db, user=user, agent_id=agent_id, skill_id=skill_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow skill not found on the selected agent.",
        )

    skill_type = _get_skill_type_from_assignment(assignment)
    if skill_type != "workflow_skill":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill must be a workflow_skill.",
        )

    if getattr(assignment, "is_enabled", None) is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow skill must be active.",
        )

    return binding, assignment


def _build_execution_response(
    *,
    template: dict,
    status_value: str,
    success: bool,
    execution_id,
    output_summary: str | None,
    error_message: str | None,
    http_status_code: int | None,
) -> WorkflowExecutionResponse:
    return WorkflowExecutionResponse(
        success=success,
        status=status_value,
        template_id=str(template["id"]),
        template_version=str(template["template_version"]),
        execution_id=str(execution_id) if execution_id is not None else None,
        output_summary=output_summary,
        error_message=error_message,
        http_status_code=http_status_code,
    )


def execute_workflow_template(
    db: Session,
    *,
    user,
    template_id: str,
    request: WorkflowExecutionRequest,
) -> WorkflowExecutionResponse:
    # This path never trusts frontend suggestion metadata; consent and bindings are
    # revalidated server-side before the webhook is called.
    _require_owner_access(user)
    _rate_limit_bucket(user.id, "execute", WORKFLOW_EXECUTE_RATE_LIMIT_MAX_REQUESTS)

    template = _load_workflow_template_or_404(template_id)
    _ensure_template_enabled(template)
    _ensure_template_url_safe(template)

    try:
        agent_id = uuid.UUID(request.agent_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid agent_id.")

    try:
        skill_id = uuid.UUID(request.skill_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid skill_id.")

    agent = _load_agent_for_execution(db, user=user, agent_id=agent_id)
    _load_owned_workflow_skill_binding(
        db,
        user=user,
        agent_id=agent.id,
        skill_id=skill_id,
        template_id=template_id,
        template_version=str(template["template_version"]),
    )

    consent = workflow_consent_repository.get_consent(
        db,
        user_id=user.id,
        template_id=template_id,
        template_version=str(template["template_version"]),
    )
    if consent is None:
        return _build_execution_response(
            template=template,
            status_value="consent_required",
            success=False,
            execution_id=None,
            output_summary=None,
            error_message="Consent is required before this workflow can run.",
            http_status_code=428,
        )

    try:
        sanitized_payload = sanitize_payload_for_template(template, request.input_payload)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input payload exceeds maximum size for this template.",
        )

    canonical_webhook_url = canonicalize_webhook_url(str(template["webhook_url"]))
    webhook_result: WebhookCallResult = call_template_webhook(canonical_webhook_url, sanitized_payload)

    if webhook_result.timed_out:
        execution_status = "timeout"
        success = False
        error_message = webhook_result.error_message or "Webhook request timed out."
    elif webhook_result.success:
        execution_status = "success"
        success = True
        error_message = None
    else:
        execution_status = "failed"
        success = False
        error_message = webhook_result.error_message or "Webhook request failed."

    output_summary = webhook_result.response_summary
    if success and not output_summary:
        output_summary = "Workflow webhook completed successfully."

    execution = workflow_execution_repository.create_execution(
        db,
        {
            "user_id": user.id,
            "agent_id": agent.id,
            "skill_id": skill_id,
            "template_id": template_id,
            "template_version": str(template["template_version"]),
            "consent_id": consent.id,
            "webhook_url": canonical_webhook_url,
            "input_payload_sanitized": sanitized_payload,
            "output_summary": output_summary,
            "status": execution_status,
            "error_message": sanitize_error_message(error_message) if error_message else None,
            "http_status_code": webhook_result.status_code,
        },
    )
    db.commit()
    db.refresh(execution)

    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=user.id,
        request_id=None,
        event_type="workflow.execute.recorded",
        message="Workflow template execution recorded.",
        metadata_json={
            "user_id": str(user.id),
            "agent_id": str(agent.id),
            "skill_id": str(skill_id),
            "template_id": template_id,
            "template_version": str(template["template_version"]),
            "execution_id": str(execution.id),
            "status": execution_status,
            "success": success,
            "http_status_code": webhook_result.status_code,
            "response_truncated": webhook_result.response_truncated,
        },
    )
    db.commit()

    return _build_execution_response(
        template=template,
        status_value=execution_status,
        success=success,
        execution_id=execution.id,
        output_summary=output_summary,
        error_message=sanitize_error_message(error_message) if error_message else None,
        http_status_code=webhook_result.status_code,
    )


def execute_workflow_template_from_chat_confirmation(
    db: Session,
    *,
    user,
    template_id: str,
    request: WorkflowChatExecutionRequest,
) -> WorkflowExecutionResponse:
    # Chat confirmation must be explicit per run and then reuse the same execution
    # validation path as manual execution.
    if not request.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit confirmation is required before executing a workflow.",
        )
    if request.confirmation_source != "chat_suggestion":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow confirmation source.",
        )

    execution_request = WorkflowExecutionRequest(
        agent_id=request.agent_id,
        skill_id=request.skill_id,
        input_payload=request.input_payload,
    )
    return execute_workflow_template(
        db,
        user=user,
        template_id=template_id,
        request=execution_request,
    )
