import re
import uuid
from types import SimpleNamespace

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.subscription_plans import is_admin_role
from app.repositories import agent_repository, handoff_draft_repository
from app.schemas.handoff_draft import (
    HandoffDraftAgentResponse,
    HandoffDraftCreateRequest,
    HandoffDraftListResponse,
    HandoffDraftPayloadResponse,
    HandoffDraftResponse,
    HandoffDraftSkillMatchResponse,
)
from app.services.agent_routing_service import preview_agent_routing


MAX_DRAFT_TASK_SUMMARY_LENGTH = 220
MAX_DRAFT_LIMIT = 100
DEFAULT_DRAFT_LIMIT = 20


def _normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _truncate_text(value: str, limit: int) -> str:
    normalized = _normalize_text(value)
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(limit - 1, 0)].rstrip() + "…"


def _get_value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _build_agent_summary(agent) -> HandoffDraftAgentResponse:
    return HandoffDraftAgentResponse(
        agent_id=_get_value(agent, "agent_id", _get_value(agent, "id")),
        name=_get_value(agent, "name", "Unknown agent"),
        slug=_get_value(agent, "slug", ""),
        description=_get_value(agent, "description"),
        role_description=_get_value(agent, "role_description"),
    )


def _build_skill_match_payload(match) -> dict:
    return {
        "skill_id": str(_get_value(match, "skill_id", _get_value(match, "id"))),
        "title": _get_value(match, "title", "Matched skill"),
        "skill_type": _get_value(match, "skill_type", "prompt_skill"),
        "match_reason": _get_value(match, "reason", ""),
    }


def _build_skill_match_response(match) -> HandoffDraftSkillMatchResponse:
    return HandoffDraftSkillMatchResponse(
        skill_id=_get_value(match, "skill_id", _get_value(match, "id")),
        title=_get_value(match, "title", "Matched skill"),
        skill_type=_get_value(match, "skill_type", "prompt_skill"),
        match_reason=_get_value(match, "match_reason", _get_value(match, "reason", "")),
    )


def _build_candidate_lookup(candidates) -> dict[str, object]:
    lookup: dict[str, object] = {}
    for candidate in candidates or []:
        agent_id = _get_value(candidate, "agent_id", None)
        if agent_id is not None:
            lookup[str(agent_id)] = candidate
    return lookup


def _resolve_accessible_agent(db: Session, *, owner_id: uuid.UUID, agent_id: uuid.UUID, current_user):
    if is_admin_role(_get_value(current_user, "role")):
        agent = agent_repository.get_by_id_for_admin(db, agent_id)
    else:
        agent = agent_repository.get_by_id(db, owner_id, agent_id)

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    return agent


def _resolve_draft_for_access(db: Session, *, owner_id: uuid.UUID, draft_id: uuid.UUID, current_user):
    if is_admin_role(_get_value(current_user, "role")):
        draft = handoff_draft_repository.get_by_id(db, draft_id)
    else:
        draft = handoff_draft_repository.get_by_id_for_owner(db, draft_id, owner_id)

    if draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Handoff draft not found.",
        )

    return draft


def _load_agent_summary(db: Session, *, owner_id: uuid.UUID, agent_id: uuid.UUID | None, current_user):
    if agent_id is None:
        return None

    if is_admin_role(_get_value(current_user, "role")):
        return agent_repository.get_by_id_for_admin(db, agent_id)
    return agent_repository.get_by_id(db, owner_id, agent_id)


def _build_draft_payload(task_text: str, *, selected_agent_name: str, matched_skill_titles: list[str]) -> HandoffDraftPayloadResponse:
    task_summary = _truncate_text(task_text, MAX_DRAFT_TASK_SUMMARY_LENGTH)
    matched_summary = ", ".join(matched_skill_titles[:3]) if matched_skill_titles else "none"
    handoff_message = (
        f"Handoff draft for {selected_agent_name}. "
        f"Task summary: {task_summary}. "
        f"Matched active skills: {matched_summary}. "
        "This is a draft only and must not execute."
    )
    suggested_steps = [
        "Review the task and confirm the requested outcome.",
        "Use the attached active skills as instruction or capability context only.",
        "Prepare a safe response draft for the user.",
        "Do not execute runtime, tools, workflows, or external calls.",
    ]
    if matched_skill_titles:
        suggested_steps.insert(
            2,
            "Use the matched skills as active guidance: " + ", ".join(matched_skill_titles[:3]) + ".",
        )

    return HandoffDraftPayloadResponse(
        task_summary=task_summary,
        handoff_message=handoff_message,
        suggested_steps=suggested_steps,
        safety_note="Draft only, no execution.",
    )


def _build_handoff_draft_response(draft, *, recommended_agent, selected_agent, active_skill_matches) -> HandoffDraftResponse:
    return HandoffDraftResponse(
        id=draft.id,
        owner_id=draft.owner_id,
        task_text=draft.task_text,
        routing_confidence=draft.routing_confidence,
        routing_reasons=list(draft.routing_reasons or []),
        recommended_agent_id=draft.recommended_agent_id,
        selected_agent_id=draft.selected_agent_id,
        active_skill_matches=[_build_skill_match_response(match) for match in (active_skill_matches or [])],
        draft_payload=HandoffDraftPayloadResponse.model_validate(draft.draft_payload),
        status=draft.status,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
        recommended_agent=_build_agent_summary(recommended_agent) if recommended_agent else None,
        selected_agent=_build_agent_summary(selected_agent) if selected_agent else None,
    )


def _select_candidate(candidates, agent_id: uuid.UUID):
    candidate_lookup = _build_candidate_lookup(candidates)
    return candidate_lookup.get(str(agent_id))


def create_handoff_draft(
    db: Session,
    *,
    owner_id: uuid.UUID,
    payload: HandoffDraftCreateRequest,
    current_user,
) -> HandoffDraftResponse:
    task_text = payload.task_text.strip()
    if not task_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task text is required.",
        )

    selected_agent = None
    if payload.selected_agent_id is not None:
        selected_agent = _resolve_accessible_agent(
            db,
            owner_id=owner_id,
            agent_id=payload.selected_agent_id,
            current_user=current_user,
        )

    routing_preview = preview_agent_routing(db, current_user=current_user, task_text=task_text)
    recommended_candidate = routing_preview.recommended_agent
    candidate_agents = list(routing_preview.candidate_agents or [])

    if selected_agent is None:
        if recommended_candidate is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No accessible agents found for this task.",
            )
        selected_candidate = recommended_candidate
        selected_agent = _resolve_accessible_agent(
            db,
            owner_id=owner_id,
            agent_id=selected_candidate.agent_id,
            current_user=current_user,
        )
    else:
        selected_candidate = _select_candidate(candidate_agents, selected_agent.id)
        if selected_candidate is None:
            selected_candidate = SimpleNamespace(
                agent_id=selected_agent.id,
                name=selected_agent.name,
                slug=selected_agent.slug,
                description=selected_agent.description,
                role_description=selected_agent.role_description,
                active_skill_matches=[],
            )

    active_skill_matches = list(getattr(selected_candidate, "active_skill_matches", []) or [])
    matched_skill_titles = [
        _get_value(match, "title", "Matched skill")
        for match in active_skill_matches
    ]

    draft = handoff_draft_repository.create(
        db,
        {
            "owner_id": owner_id,
            "task_text": task_text,
            "routing_confidence": routing_preview.confidence,
            "routing_reasons": list(routing_preview.reasons or []),
            "recommended_agent_id": _get_value(recommended_candidate, "agent_id", None),
            "selected_agent_id": selected_agent.id,
            "active_skill_matches": [_build_skill_match_payload(match) for match in active_skill_matches],
            "draft_payload": _build_draft_payload(
                task_text,
                selected_agent_name=selected_agent.name,
                matched_skill_titles=matched_skill_titles,
            ).model_dump(),
            "status": "draft",
        },
    )
    db.commit()
    db.refresh(draft)
    return _build_handoff_draft_response(
        draft,
        recommended_agent=recommended_candidate,
        selected_agent=selected_candidate,
        active_skill_matches=active_skill_matches,
    )


def list_handoff_drafts(
    db: Session,
    *,
    owner_id: uuid.UUID,
    current_user,
    limit: int = DEFAULT_DRAFT_LIMIT,
    offset: int = 0,
) -> HandoffDraftListResponse:
    safe_limit = max(1, min(int(limit), MAX_DRAFT_LIMIT))
    safe_offset = max(0, int(offset))
    if is_admin_role(_get_value(current_user, "role")):
        drafts = handoff_draft_repository.list_all(db, limit=safe_limit, offset=safe_offset)
    else:
        drafts = handoff_draft_repository.list_by_owner(db, owner_id, limit=safe_limit, offset=safe_offset)

    items = [
        _build_handoff_draft_response(
            draft,
            recommended_agent=_load_agent_summary(
                db,
                owner_id=owner_id,
                agent_id=draft.recommended_agent_id,
                current_user=current_user,
            ),
            selected_agent=_load_agent_summary(
                db,
                owner_id=owner_id,
                agent_id=draft.selected_agent_id,
                current_user=current_user,
            ),
            active_skill_matches=draft.active_skill_matches or [],
        )
        for draft in drafts
    ]
    return HandoffDraftListResponse(items=items)


def get_handoff_draft(
    db: Session,
    *,
    owner_id: uuid.UUID,
    draft_id: uuid.UUID,
    current_user,
) -> HandoffDraftResponse:
    draft = _resolve_draft_for_access(
        db,
        owner_id=owner_id,
        draft_id=draft_id,
        current_user=current_user,
    )
    return _build_handoff_draft_response(
        draft,
        recommended_agent=_load_agent_summary(
            db,
            owner_id=owner_id,
            agent_id=draft.recommended_agent_id,
            current_user=current_user,
        ),
        selected_agent=_load_agent_summary(
            db,
            owner_id=owner_id,
            agent_id=draft.selected_agent_id,
            current_user=current_user,
        ),
        active_skill_matches=draft.active_skill_matches or [],
    )


def archive_handoff_draft(
    db: Session,
    *,
    owner_id: uuid.UUID,
    draft_id: uuid.UUID,
    current_user,
) -> HandoffDraftResponse:
    draft = _resolve_draft_for_access(
        db,
        owner_id=owner_id,
        draft_id=draft_id,
        current_user=current_user,
    )
    if draft.status == "archived":
        return _build_handoff_draft_response(
            draft,
            recommended_agent=_load_agent_summary(
                db,
                owner_id=owner_id,
                agent_id=draft.recommended_agent_id,
                current_user=current_user,
            ),
            selected_agent=_load_agent_summary(
                db,
                owner_id=owner_id,
                agent_id=draft.selected_agent_id,
                current_user=current_user,
            ),
            active_skill_matches=draft.active_skill_matches or [],
        )

    draft = handoff_draft_repository.update(db, draft, {"status": "archived"})
    db.commit()
    db.refresh(draft)
    return _build_handoff_draft_response(
        draft,
        recommended_agent=_load_agent_summary(
            db,
            owner_id=owner_id,
            agent_id=draft.recommended_agent_id,
            current_user=current_user,
        ),
        selected_agent=_load_agent_summary(
            db,
            owner_id=owner_id,
            agent_id=draft.selected_agent_id,
            current_user=current_user,
        ),
        active_skill_matches=draft.active_skill_matches or [],
    )
