from __future__ import annotations

import threading
import time
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.agent import AgentRoutingPreviewResponse
from app.schemas.agent_chat import AgentChatRequest
from app.schemas.orchestrator import OrchestratorRequest, OrchestratorResponse
from app.services import agent_chat_service, agent_routing_service, log_service
from app.services import session_service


ORCHESTRATOR_FALLBACK_REPLY = (
    "Maaf, saya tidak menemukan agent yang sesuai untuk task ini. "
    "Silakan coba kata kunci yang berbeda atau tambahkan agent baru."
)
ORCHESTRATOR_RATE_LIMIT_MAX_REQUESTS = 20
ORCHESTRATOR_RATE_LIMIT_WINDOW_SECONDS = 60
ORCHESTRATOR_RATE_LIMIT_MESSAGE = "Terlalu banyak pesan, tunggu sebentar"

_rate_limit_lock = threading.Lock()
_rate_limit_state: dict[str, list[float]] = {}


def clear_orchestrator_rate_limiter() -> None:
    with _rate_limit_lock:
        _rate_limit_state.clear()


def _rate_limit_bucket(owner_id: uuid.UUID) -> list[float]:
    now = time.monotonic()
    with _rate_limit_lock:
        bucket = _rate_limit_state.setdefault(str(owner_id), [])
        bucket[:] = [timestamp for timestamp in bucket if now - timestamp < ORCHESTRATOR_RATE_LIMIT_WINDOW_SECONDS]
        if len(bucket) >= ORCHESTRATOR_RATE_LIMIT_MAX_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=ORCHESTRATOR_RATE_LIMIT_MESSAGE,
            )
        bucket.append(now)
        return bucket


def _safe_detail_message(detail) -> str:
    if isinstance(detail, str):
        return detail.strip() or ORCHESTRATOR_FALLBACK_REPLY
    message = str(detail).strip()
    return message or ORCHESTRATOR_FALLBACK_REPLY


def _log_orchestrator_attempt(
    db: Session,
    *,
    owner_id: uuid.UUID,
    session_id: uuid.UUID | None,
    routed_agent_id: str | None,
    confidence: str,
    status_name: str,
    provider: str | None,
    model: str | None,
    success: bool,
) -> None:
    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=owner_id,
        request_id=None,
        event_type="orchestrator.chat",
        message="Workspace orchestrator completed." if success else "Workspace orchestrator failed.",
        metadata_json={
            "user_id": str(owner_id),
            "session_id": str(session_id) if session_id is not None else None,
            "routed_agent_id": routed_agent_id,
            "confidence": confidence,
            "status": status_name,
            "provider": provider,
            "model": model,
            "success": success,
        },
    )
    db.commit()


def _build_chat_payload(task_text: str, messages) -> AgentChatRequest:
    chat_messages = messages if messages else [{"role": "user", "content": task_text}]
    return AgentChatRequest(messages=chat_messages)


def _normalize_orchestrator_messages(payload: OrchestratorRequest, *, task_text: str) -> list[dict]:
    return [message.model_dump() for message in payload.messages] if payload.messages else [{"role": "user", "content": task_text}]


def _route_to_agent(
    db: Session,
    *,
    owner_id: uuid.UUID,
    task_text: str,
    preview: AgentRoutingPreviewResponse,
    payload: OrchestratorRequest,
    current_user,
) -> OrchestratorResponse:
    existing_session = None
    if payload.session_id is not None:
        existing_session = session_service.load_session_for_owner(
            db,
            user_id=owner_id,
            session_id=payload.session_id,
        )
        if existing_session.session_type != session_service.SESSION_TYPE_ORCHESTRATOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session type mismatch.",
            )

    recommended_agent = preview.recommended_agent
    if recommended_agent is None or preview.confidence not in {"high", "medium"}:
        response = OrchestratorResponse(
            session_id=None,
            task_text=task_text,
            routed_to_agent_id=None,
            routed_to_agent_name=None,
            confidence="none" if recommended_agent is None else preview.confidence,
            reply=ORCHESTRATOR_FALLBACK_REPLY,
            routing_reasons=list(preview.reasons or []),
            status="fallback",
            workflow_suggestions=[],
        )
        session_summary = session_service.upsert_chat_session(
            db,
            user_id=owner_id,
            session_type=session_service.SESSION_TYPE_ORCHESTRATOR,
            messages=_normalize_orchestrator_messages(payload, task_text=task_text),
            assistant_reply=response.reply,
            agent_id=None,
            session_id=existing_session.id if existing_session is not None else None,
        )
        response.session_id = session_summary.id
        _log_orchestrator_attempt(
            db,
            owner_id=owner_id,
            session_id=response.session_id,
            routed_agent_id=None,
            confidence="none" if recommended_agent is None else preview.confidence,
            status_name="fallback",
            provider=None,
            model=None,
            success=True,
        )
        return response

    agent_id = recommended_agent.agent_id
    chat_payload = _build_chat_payload(task_text, payload.messages)

    try:
        agent_result = agent_chat_service.chat_with_agent(
            db,
            owner_id=owner_id,
            agent_id=agent_id,
            payload=chat_payload,
            current_user=current_user,
        )
        provider = getattr(agent_result, "provider", None)
        model = getattr(agent_result, "model", None)
        routed_response = OrchestratorResponse(
            session_id=None,
            task_text=task_text,
            routed_to_agent_id=str(agent_result.agent_id),
            routed_to_agent_name=agent_result.agent_name,
            confidence=preview.confidence,
            reply=agent_result.reply,
            provider=provider,
            model=model,
            prompt_skills_used=list(getattr(agent_result, "prompt_skills_used", []) or []),
            knowledge_skills_used=list(getattr(agent_result, "knowledge_skills_used", []) or []),
            knowledge_truncated=bool(getattr(agent_result, "knowledge_truncated", False)),
            workflow_suggestions=list(getattr(agent_result, "workflow_suggestions", []) or []),
            routing_reasons=list(preview.reasons or []),
            status="routed",
            warning=getattr(agent_result, "warning", None),
        )
        session_summary = session_service.upsert_chat_session(
            db,
            user_id=owner_id,
            session_type=session_service.SESSION_TYPE_ORCHESTRATOR,
            messages=_normalize_orchestrator_messages(payload, task_text=task_text),
            assistant_reply=routed_response.reply,
            agent_id=None,
            session_id=existing_session.id if existing_session is not None else None,
        )
        routed_response.session_id = session_summary.id
        _log_orchestrator_attempt(
            db,
            owner_id=owner_id,
            session_id=routed_response.session_id,
            routed_agent_id=str(agent_result.agent_id),
            confidence=preview.confidence,
            status_name="routed",
            provider=provider,
            model=model,
            success=True,
        )
        return routed_response
    except HTTPException as exc:
        safe_reply = _safe_detail_message(exc.detail)
        response = OrchestratorResponse(
            session_id=None,
            task_text=task_text,
            routed_to_agent_id=str(agent_id),
            routed_to_agent_name=getattr(recommended_agent, "name", None),
            confidence=preview.confidence,
            reply=safe_reply,
            routing_reasons=list(preview.reasons or []),
            status="routed",
            workflow_suggestions=[],
            warning=safe_reply,
        )
        session_summary = session_service.upsert_chat_session(
            db,
            user_id=owner_id,
            session_type=session_service.SESSION_TYPE_ORCHESTRATOR,
            messages=_normalize_orchestrator_messages(payload, task_text=task_text),
            assistant_reply=response.reply,
            agent_id=None,
            session_id=existing_session.id if existing_session is not None else None,
        )
        response.session_id = session_summary.id
        _log_orchestrator_attempt(
            db,
            owner_id=owner_id,
            session_id=response.session_id,
            routed_agent_id=str(agent_id),
            confidence=preview.confidence,
            status_name="routed",
            provider=None,
            model=None,
            success=False,
        )
        return response
    except Exception:
        response = OrchestratorResponse(
            session_id=None,
            task_text=task_text,
            routed_to_agent_id=str(agent_id),
            routed_to_agent_name=getattr(recommended_agent, "name", None),
            confidence=preview.confidence,
            reply=ORCHESTRATOR_FALLBACK_REPLY,
            routing_reasons=list(preview.reasons or []),
            status="routed",
            workflow_suggestions=[],
            warning=ORCHESTRATOR_FALLBACK_REPLY,
        )
        session_summary = session_service.upsert_chat_session(
            db,
            user_id=owner_id,
            session_type=session_service.SESSION_TYPE_ORCHESTRATOR,
            messages=_normalize_orchestrator_messages(payload, task_text=task_text),
            assistant_reply=response.reply,
            agent_id=None,
            session_id=existing_session.id if existing_session is not None else None,
        )
        response.session_id = session_summary.id
        _log_orchestrator_attempt(
            db,
            owner_id=owner_id,
            session_id=response.session_id,
            routed_agent_id=str(agent_id),
            confidence=preview.confidence,
            status_name="routed",
            provider=None,
            model=None,
            success=False,
        )
        return response


def orchestrate_workspace_chat(
    db: Session,
    *,
    owner_id: uuid.UUID,
    payload: OrchestratorRequest,
    current_user,
) -> OrchestratorResponse:
    _rate_limit_bucket(owner_id)
    preview = agent_routing_service.preview_agent_routing(
        db,
        current_user=current_user,
        task_text=payload.task_text,
    )
    return _route_to_agent(
        db,
        owner_id=owner_id,
        task_text=payload.task_text,
        preview=preview,
        payload=payload,
        current_user=current_user,
    )
