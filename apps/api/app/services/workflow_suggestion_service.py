from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.webhook_security import validate_safe_webhook_url
from app.core.workflow_templates import get_workflow_template, get_workflow_templates
from app.repositories import workflow_consent_repository, workflow_skill_binding_repository
from app.schemas.agent_chat import WorkflowSuggestion
from app.services import skill_service


STOPWORDS = {
    "a",
    "and",
    "for",
    "from",
    "help",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "please",
    "the",
    "to",
    "with",
    "you",
}


@dataclass(frozen=True, slots=True)
class _SuggestionCandidate:
    score: int
    template_id: str
    skill_id: str
    skill_title: str
    template_name: str
    reason: str
    consent_required: bool
    binding_exists: bool
    execution_available: bool
    created_at: datetime


def _clean_text(value) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def _normalize_text(value) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _clean_text(value).lower()).strip()


def _tokenize(value) -> set[str]:
    return {
        token
        for token in _normalize_text(value).split()
        if len(token) >= 3 and token not in STOPWORDS
    }


def _extract_skill_title(skill) -> str:
    for field_name in ("title", "name", "slug"):
        candidate = _clean_text(getattr(skill, field_name, None))
        if candidate:
            return candidate
    skill_id = getattr(skill, "id", None)
    return str(skill_id) if skill_id is not None else "Unknown skill"


def _extract_skill_summary(skill) -> str:
    for field_name in ("content", "instruction_text", "prompt", "text", "description"):
        candidate = _clean_text(getattr(skill, field_name, None))
        if candidate:
            return candidate
    return ""


def _get_skill_type(assignment) -> str | None:
    skill = getattr(assignment, "skill", None)
    if skill is None and isinstance(assignment, dict):
        skill = assignment.get("skill")

    if skill is None:
        return None

    if isinstance(skill, dict):
        skill_type = skill.get("type") or skill.get("skill_type")
    else:
        skill_type = getattr(skill, "type", None) or getattr(skill, "skill_type", None)

    return str(skill_type) if skill_type else None


def _match_score(task_text: str, skill_title: str, skill_summary: str, template_name: str, template_description: str) -> tuple[int, list[str]] | None:
    task_norm = _normalize_text(task_text)
    task_tokens = _tokenize(task_text)
    reasons: list[str] = []
    score = 0

    title_norm = _normalize_text(skill_title)
    template_name_norm = _normalize_text(template_name)

    if title_norm and title_norm in task_norm:
        score += 4
        reasons.append("Matched workflow skill title with user task")

    if template_name_norm and template_name_norm in task_norm:
        score += 4
        reasons.append("Matched workflow template name with user task")

    skill_tokens = _tokenize(f"{skill_title} {skill_summary}")
    template_tokens = _tokenize(f"{template_name} {template_description}")

    skill_overlap = sorted(task_tokens & skill_tokens)
    if skill_overlap:
        score += min(len(skill_overlap) * 2, 6)
        reasons.append("Matched workflow skill keywords with user task")

    template_overlap = sorted(task_tokens & template_tokens)
    if template_overlap:
        score += min(len(template_overlap) * 2, 6)
        reasons.append("Matched workflow template keywords with user task")

    if score <= 0:
        return None

    reasons = list(dict.fromkeys(reasons))
    return score, reasons


def _template_is_enabled_and_safe(template_id: str) -> dict | None:
    template = get_workflow_template(template_id)
    if template is None or not template.get("enabled"):
        return None

    is_safe, _reason = validate_safe_webhook_url(str(template.get("webhook_url") or ""))
    if not is_safe:
        return None

    return template


def _build_candidate(
    *,
    task_text: str,
    skill,
    template: dict,
    binding_exists: bool,
    consent_exists: bool,
) -> _SuggestionCandidate | None:
    match = _match_score(
        task_text,
        _extract_skill_title(skill),
        _extract_skill_summary(skill),
        str(template.get("name") or ""),
        str(template.get("description") or ""),
    )
    if match is None:
        return None

    score, reasons = match
    if binding_exists:
        score += 10
    if consent_exists:
        score += 5

    return _SuggestionCandidate(
        score=score,
        template_id=str(template["id"]),
        skill_id=str(getattr(skill, "id", "")),
        skill_title=_extract_skill_title(skill),
        template_name=str(template.get("name") or template["id"]),
        reason="; ".join(reasons[:2]) if reasons else "Matched workflow skill with task",
        consent_required=not consent_exists,
        binding_exists=binding_exists,
        execution_available=bool(binding_exists and consent_exists and template.get("enabled")),
        created_at=getattr(skill, "created_at", None) or datetime.min.replace(tzinfo=UTC),
    )


def get_workflow_suggestions_for_agent(
    db: Session,
    *,
    user,
    agent_id: uuid.UUID,
    task_text: str,
) -> list[WorkflowSuggestion]:
    normalized_task_text = _clean_text(task_text)
    if not normalized_task_text:
        return []

    active_skills = skill_service.list_active_agent_skills(
        db,
        owner_id=user.id,
        agent_id=agent_id,
        current_user=user,
    )
    if not active_skills:
        return []

    enabled_templates = get_workflow_templates(include_disabled=False)
    if not enabled_templates:
        return []

    bindings = workflow_skill_binding_repository.list_bindings(db, user_id=user.id)
    consents = {
        (consent.template_id, consent.template_version)
        for consent in workflow_consent_repository.list_consents(db, user_id=user.id)
    }

    binding_index: dict[tuple[str, str], object] = {}
    for binding in bindings:
        binding_index[(str(binding.skill_id), str(binding.template_id))] = binding

    candidates: list[_SuggestionCandidate] = []
    for assignment in active_skills:
        if not assignment or not getattr(assignment, "is_enabled", False):
            continue
        skill = getattr(assignment, "skill", None)
        if skill is None:
            continue
        if getattr(skill, "deleted_at", None) is not None or getattr(skill, "status", None) != "active":
            continue
        if _get_skill_type(assignment) != "workflow_skill":
            continue

        skill_id = str(getattr(skill, "id", ""))
        for template_record in enabled_templates:
            template = _template_is_enabled_and_safe(str(template_record["id"]))
            if template is None:
                continue

            binding = binding_index.get((skill_id, str(template["id"])))
            binding_exists = bool(binding and str(getattr(binding, "template_version", "")) == str(template["template_version"]))
            consent_exists = (str(template["id"]), str(template["template_version"])) in consents

            candidate = _build_candidate(
                task_text=normalized_task_text,
                skill=skill,
                template=template,
                binding_exists=binding_exists,
                consent_exists=consent_exists,
            )
            if candidate is None:
                continue
            candidates.append(candidate)

    candidates.sort(
        key=lambda item: (
            -item.score,
            item.template_name.lower(),
            item.skill_title.lower(),
            item.template_id,
            item.skill_id,
        )
    )

    deduped: list[_SuggestionCandidate] = []
    seen_templates: set[str] = set()
    for candidate in candidates:
        if candidate.template_id in seen_templates:
            continue
        seen_templates.add(candidate.template_id)
        deduped.append(candidate)
        if len(deduped) >= 3:
            break

    return [
        WorkflowSuggestion(
            template_id=candidate.template_id,
            template_name=candidate.template_name,
            skill_id=candidate.skill_id,
            skill_title=candidate.skill_title,
            reason=candidate.reason,
            consent_required=candidate.consent_required,
            binding_exists=candidate.binding_exists,
            execution_available=candidate.execution_available,
        )
        for candidate in deduped
    ]
