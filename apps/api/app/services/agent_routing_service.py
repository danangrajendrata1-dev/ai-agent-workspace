import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.subscription_plans import is_admin_role
from app.repositories import agent_repository
from app.schemas.agent import (
    AgentRoutingCandidateResponse,
    AgentRoutingPreviewResponse,
    AgentRoutingSkillMatchResponse,
)
from app.services import skill_service


STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "ask",
    "be",
    "for",
    "from",
    "help",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "please",
    "task",
    "the",
    "to",
    "with",
    "work",
    "workspace",
    "you",
}

SKILL_TYPE_HINTS: dict[str, set[str]] = {
    "prompt_skill": {"chat", "draft", "explain", "prompt", "rewrite", "summarize", "write"},
    "knowledge_skill": {"answer", "doc", "docs", "document", "faq", "knowledge", "reference", "research", "summary"},
    "tool_skill": {"action", "api", "browser", "file", "github", "repo", "search", "tool", "transform"},
    "workflow_skill": {"automation", "automate", "flow", "n8n", "pipeline", "process", "workflow"},
}

MAX_CANDIDATES = 5


@dataclass(slots=True)
class _ScoredCandidate:
    score: int
    agent: object
    reasons: list[str]
    skill_matches: list[AgentRoutingSkillMatchResponse]


def _normalize_text(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _tokenize(value: str | None) -> set[str]:
    return {
        token
        for token in _normalize_text(value).split()
        if len(token) >= 3 and token not in STOPWORDS
    }


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _score_overlap(task_tokens: set[str], text: str | None, *, weight: int, cap: int) -> tuple[int, list[str]]:
    overlap = sorted(task_tokens & _tokenize(text))
    if not overlap:
        return 0, []
    return min(len(overlap) * weight, cap), overlap


def _score_skill_match(task_text: str, task_tokens: set[str], skill) -> AgentRoutingSkillMatchResponse | None:
    title = getattr(skill, "title", "") or ""
    skill_type = getattr(skill, "skill_type", "prompt_skill") or "prompt_skill"
    status = getattr(skill, "status", "inactive") or "inactive"
    security_status = getattr(skill, "security_status", "safe") or "safe"

    score = 0
    matched_terms: list[str] = []
    reasons: list[str] = []
    normalized_title = _normalize_text(title)
    task_norm = _normalize_text(task_text)

    if normalized_title and normalized_title in task_norm:
        score += 25
        matched_terms.append(title)
        reasons.append(f"Task mentions active skill '{title}'.")

    title_overlap_score, title_overlap_terms = _score_overlap(task_tokens, title, weight=5, cap=15)
    if title_overlap_terms:
        score += title_overlap_score
        matched_terms.extend(title_overlap_terms)
        reasons.append(f"Shared skill terms: {', '.join(title_overlap_terms)}.")

    type_hits = sorted(term for term in SKILL_TYPE_HINTS.get(skill_type, set()) if term in task_tokens)
    if type_hits:
        score += 12
        matched_terms.extend(type_hits)
        reasons.append(f"Task suggests {skill_type.replace('_', ' ')} work.")

    matched_terms = sorted(dict.fromkeys(matched_terms))
    if score <= 0:
        return None

    return AgentRoutingSkillMatchResponse(
        skill_id=skill.id,
        title=title,
        skill_type=skill_type,
        status=status,
        security_status=security_status,
        matched_terms=matched_terms,
        match_score=score,
        reason=" ".join(reasons),
    )


def _score_agent(task_text: str, agent, active_skills) -> _ScoredCandidate:
    task_norm = _normalize_text(task_text)
    task_tokens = _tokenize(task_text)
    score = 0
    reasons: list[str] = []
    skill_matches: list[AgentRoutingSkillMatchResponse] = []

    agent_name_norm = _normalize_text(getattr(agent, "name", ""))
    if agent_name_norm and agent_name_norm in task_norm:
        score += 35
        reasons.append(f"Task mentions agent name '{agent.name}'.")

    name_score, name_terms = _score_overlap(task_tokens, getattr(agent, "name", ""), weight=6, cap=18)
    if name_terms:
        score += name_score
        reasons.append(f"Agent name overlaps with task terms: {', '.join(name_terms)}.")

    description_text = " ".join(
        value for value in [getattr(agent, "description", None), getattr(agent, "role_description", None)] if value
    )
    description_score, description_terms = _score_overlap(task_tokens, description_text, weight=3, cap=12)
    if description_terms:
        score += description_score
        reasons.append(f"Agent description overlaps with task terms: {', '.join(description_terms)}.")

    for skill in active_skills:
        skill_match = _score_skill_match(task_text, task_tokens, skill.skill)
        if skill_match is None:
            continue
        skill_matches.append(skill_match)
        score += skill_match.match_score
        reasons.append(f"Active skill match: {skill_match.title}.")

    reasons = _dedupe_preserve_order(reasons)
    if not reasons:
        reasons = ["No strong keyword overlap found."]

    return _ScoredCandidate(
        score=score,
        agent=agent,
        reasons=reasons,
        skill_matches=skill_matches,
    )


def _get_routable_agents(db: Session, current_user) -> list[object]:
    if is_admin_role(getattr(current_user, "role", None)):
        return agent_repository.list_all_active(db)
    return agent_repository.list_by_owner(db, current_user.id)


def _build_candidate_response(candidate: _ScoredCandidate) -> AgentRoutingCandidateResponse:
    agent = candidate.agent
    return AgentRoutingCandidateResponse(
        agent_id=agent.id,
        name=agent.name,
        slug=agent.slug,
        description=getattr(agent, "description", None),
        role_description=getattr(agent, "role_description", None),
        score=candidate.score,
        reasons=candidate.reasons,
        active_skill_matches=candidate.skill_matches,
    )


def _calculate_confidence(best_score: int, second_best_score: int) -> str:
    if best_score >= 55 and (best_score - second_best_score >= 10 or best_score >= 70):
        return "high"
    if best_score >= 25:
        return "medium"
    return "low"


def preview_agent_routing(
    db: Session,
    *,
    current_user,
    task_text: str,
) -> AgentRoutingPreviewResponse:
    normalized_task_text = task_text.strip()
    agents = _get_routable_agents(db, current_user)

    if not agents:
        return AgentRoutingPreviewResponse(
            task_text=normalized_task_text,
            recommended_agent=None,
            candidate_agents=[],
            confidence="low",
            reasons=["No accessible agents found."],
            active_skill_matches=[],
            note="Preview only, no execution. Add an agent to see routing suggestions.",
        )

    scored_candidates: list[_ScoredCandidate] = []
    for agent in agents:
        active_skills = skill_service.list_active_agent_skills(
            db,
            owner_id=agent.owner_id,
            agent_id=agent.id,
            current_user=current_user,
        )
        scored_candidates.append(_score_agent(normalized_task_text, agent, active_skills))

    scored_candidates.sort(key=lambda item: (-item.score, str(item.agent.name).lower(), str(item.agent.slug).lower()))
    candidate_responses = [_build_candidate_response(candidate) for candidate in scored_candidates[:MAX_CANDIDATES]]

    best_candidate = candidate_responses[0] if candidate_responses else None
    best_score = scored_candidates[0].score if scored_candidates else 0
    second_best_score = scored_candidates[1].score if len(scored_candidates) > 1 else 0
    confidence = _calculate_confidence(best_score, second_best_score)

    if best_candidate is None:
        return AgentRoutingPreviewResponse(
            task_text=normalized_task_text,
            recommended_agent=None,
            candidate_agents=[],
            confidence="low",
            reasons=["No accessible agents found."],
            active_skill_matches=[],
            note="Preview only, no execution. Add an agent to see routing suggestions.",
        )

    recommended_agent = best_candidate
    reasons = recommended_agent.reasons[:3] or ["No strong keyword overlap found."]
    note = "Preview only, no execution."
    if confidence == "low":
        note = f"{note} Ask the user to choose an agent manually if the match is unclear."

    return AgentRoutingPreviewResponse(
        task_text=normalized_task_text,
        recommended_agent=recommended_agent,
        candidate_agents=candidate_responses,
        confidence=confidence,
        reasons=reasons,
        active_skill_matches=recommended_agent.active_skill_matches,
        note=note,
    )
