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


def _route_to_agent(
    db: Session,
    *,
    owner_id: uuid.UUID,
    task_text: str,
    preview: AgentRoutingPreviewResponse,
    payload: OrchestratorRequest,
    current_user,
) -> OrchestratorResponse:
    recommended_agent = preview.recommended_agent
    if recommended_agent is None or preview.confidence not in {"high", "medium"}:
        _log_orchestrator_attempt(
            db,
            owner_id=owner_id,
            routed_agent_id=None,
            confidence="none" if recommended_agent is None else preview.confidence,
            status_name="fallback",
            provider=None,
            model=None,
            success=True,
        )
        return OrchestratorResponse(
            task_text=task_text,
            routed_to_agent_id=None,
            routed_to_agent_name=None,
            confidence="none" if recommended_agent is None else preview.confidence,
            reply=ORCHESTRATOR_FALLBACK_REPLY,
            routing_reasons=list(preview.reasons or []),
            status="fallback",
        )

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
            routing_reasons=list(preview.reasons or []),
            status="routed",
            warning=getattr(agent_result, "warning", None),
        )
        _log_orchestrator_attempt(
            db,
            owner_id=owner_id,
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
        _log_orchestrator_attempt(
            db,
            owner_id=owner_id,
            routed_agent_id=str(agent_id),
            confidence=preview.confidence,
            status_name="routed",
            provider=None,
            model=None,
            success=False,
        )
        return OrchestratorResponse(
            task_text=task_text,
            routed_to_agent_id=str(agent_id),
            routed_to_agent_name=getattr(recommended_agent, "name", None),
            confidence=preview.confidence,
            reply=safe_reply,
            routing_reasons=list(preview.reasons or []),
            status="routed",
            warning=safe_reply,
        )
    except Exception:
        _log_orchestrator_attempt(
            db,
            owner_id=owner_id,
            routed_agent_id=str(agent_id),
            confidence=preview.confidence,
            status_name="routed",
            provider=None,
            model=None,
            success=False,
        )
        return OrchestratorResponse(
            task_text=task_text,
            routed_to_agent_id=str(agent_id),
            routed_to_agent_name=getattr(recommended_agent, "name", None),
            confidence=preview.confidence,
            reply=ORCHESTRATOR_FALLBACK_REPLY,
            routing_reasons=list(preview.reasons or []),
            status="routed",
            warning=ORCHESTRATOR_FALLBACK_REPLY,
        )


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
