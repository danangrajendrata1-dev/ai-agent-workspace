import re

from sqlalchemy.orm import Session

from app.schemas.agent import TaskDraftResponse, TaskDraftSkillMatch
from app.services.agent_routing_service import preview_agent_routing


SAFE_SAFETY_NOTE = "This is a draft preview only. No agent has been run. No skill has been executed."
TASK_SUMMARY_LIMIT = 220


def _normalize_spacing(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _build_task_summary(task_text: str) -> str:
    normalized = _normalize_spacing(task_text)
    if len(normalized) <= TASK_SUMMARY_LIMIT:
        return normalized
    return normalized[: TASK_SUMMARY_LIMIT - 3].rstrip() + "..."


def _build_relevant_skills(selected_agent) -> list[TaskDraftSkillMatch]:
    relevant_skills: list[TaskDraftSkillMatch] = []
    for match in getattr(selected_agent, "active_skill_matches", []) or []:
        relevance_note = getattr(match, "reason", "") or f"Relevant active skill: {getattr(match, 'title', 'Matched skill')}."
        relevant_skills.append(
            TaskDraftSkillMatch(
                skill_id=str(getattr(match, "skill_id", "")),
                title=getattr(match, "title", "Matched skill"),
                skill_type=getattr(match, "skill_type", "prompt_skill"),
                relevance_note=relevance_note,
            )
        )
    return relevant_skills


def _build_candidate_agents(candidate_agents) -> list[dict]:
    return [candidate.model_dump(mode="json") for candidate in candidate_agents or []]


def _build_selected_agent_id(selected_agent) -> str | None:
    if selected_agent is None:
        return None
    return str(getattr(selected_agent, "agent_id", None) or getattr(selected_agent, "id", None) or "")


def create_agent_task_draft(
    db: Session,
    *,
    current_user,
    task_text: str,
) -> TaskDraftResponse:
    normalized_task_text = _normalize_spacing(task_text)
    routing_preview = preview_agent_routing(
        db,
        current_user=current_user,
        task_text=normalized_task_text,
    )

    selected_agent = routing_preview.recommended_agent
    confidence = routing_preview.confidence if selected_agent is not None else "none"
    relevant_skills = _build_relevant_skills(selected_agent) if selected_agent is not None else []

    return TaskDraftResponse(
        task_text=normalized_task_text,
        selected_agent_id=_build_selected_agent_id(selected_agent),
        selected_agent_name=getattr(selected_agent, "name", None) if selected_agent is not None else None,
        confidence=confidence,
        reasons=list(routing_preview.reasons or []),
        relevant_skills=relevant_skills,
        task_summary=_build_task_summary(normalized_task_text),
        safety_note=SAFE_SAFETY_NOTE,
        status="draft_only",
        candidate_agents=_build_candidate_agents(routing_preview.candidate_agents),
    )
