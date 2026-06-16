from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.provider_api_keys import decrypt_api_key, normalize_provider_id
from app.core.provider_settings import (
    MODEL_PROVIDER_ANTHROPIC,
    MODEL_PROVIDER_GOOGLE_GEMINI,
    MODEL_PROVIDER_OPENAI,
    MODEL_PROVIDER_OPENROUTER,
)
from app.core.subscription_plans import is_admin_role
from app.repositories import (
    agent_repository,
    agent_skill_repository,
    github_import_repository,
    model_provider_api_key_repository,
    model_provider_setting_repository,
)
from app.schemas.agent_chat import AgentChatRequest, AgentChatResponse
from app.services import log_service
from app.services.github_import_service import serialize_github_import
from app.services import session_service


CHAT_DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."
CHAT_KNOWLEDGE_CONTEXT_HEADER = "--- KNOWLEDGE CONTEXT ---"
CHAT_KNOWLEDGE_CONTEXT_FOOTER = "--- END KNOWLEDGE CONTEXT ---"
CHAT_KNOWLEDGE_CONTEXT_CHAR_LIMIT = 8000
CHAT_RATE_LIMIT_MAX_REQUESTS = 20
CHAT_RATE_LIMIT_WINDOW_SECONDS = 60
CHAT_RATE_LIMIT_MESSAGE = "Terlalu banyak pesan, tunggu sebentar"
CHAT_UNSUPPORTED_PROVIDER_MESSAGE = "Provider not supported"
CHAT_NO_PROVIDER_MESSAGE = "No LLM provider configured for this agent"
CHAT_NO_API_KEY_MESSAGE = "No API key found. Please configure your provider first."
CHAT_UNAUTHORIZED_MESSAGE = "Invalid API key or unauthorized"
CHAT_SUPPORTED_PROVIDERS = {
    MODEL_PROVIDER_OPENAI,
    MODEL_PROVIDER_ANTHROPIC,
    MODEL_PROVIDER_GOOGLE_GEMINI,
    MODEL_PROVIDER_OPENROUTER,
}

_rate_limit_lock = threading.Lock()
_rate_limit_state: dict[str, list[float]] = {}


class AgentChatProviderError(RuntimeError):
    pass


class AgentChatUnauthorizedError(AgentChatProviderError):
    pass


def clear_agent_chat_rate_limiter() -> None:
    with _rate_limit_lock:
        _rate_limit_state.clear()


def _rate_limit_bucket(owner_id: uuid.UUID) -> list[float]:
    now = time.monotonic()
    with _rate_limit_lock:
        bucket = _rate_limit_state.setdefault(str(owner_id), [])
        bucket[:] = [timestamp for timestamp in bucket if now - timestamp < CHAT_RATE_LIMIT_WINDOW_SECONDS]
        if len(bucket) >= CHAT_RATE_LIMIT_MAX_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=CHAT_RATE_LIMIT_MESSAGE,
            )
        bucket.append(now)
        return bucket


def _resolve_agent_for_chat(db: Session, *, owner_id: uuid.UUID, agent_id: uuid.UUID, current_user=None):
    if current_user is not None and is_admin_role(getattr(current_user, "role", None)):
        agent = agent_repository.get_by_id_for_admin(db, agent_id)
    else:
        agent = agent_repository.get_by_id(db, owner_id, agent_id)

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    return agent


def _load_provider_configuration(db: Session, *, owner_id: uuid.UUID) -> tuple[str, str]:
    setting = model_provider_setting_repository.get_by_owner_id(db, owner_id)
    if (
        setting is None
        or not getattr(setting, "preferred_provider", None)
        or not getattr(setting, "preferred_model", None)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=CHAT_NO_PROVIDER_MESSAGE,
        )

    provider = normalize_provider_id(setting.preferred_provider)
    if provider not in CHAT_SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=CHAT_UNSUPPORTED_PROVIDER_MESSAGE,
        )

    return provider, setting.preferred_model


def _load_github_import_data(db: Session, skill) -> dict | None:
    if getattr(skill, "source_type", None) != "github" or getattr(skill, "source_id", None) is None:
        return None

    github_import = github_import_repository.get_by_id(db, skill.source_id)
    if github_import is None:
        return None

    return serialize_github_import(github_import).model_dump()


def _infer_skill_type(skill, github_import_data: dict | None) -> str:
    if not github_import_data:
        return "prompt_skill"

    import_type = github_import_data.get("skill_import_type")
    content_preview = str(github_import_data.get("content_preview") or "").lower()
    resource_paths = github_import_data.get("resource_paths") or []
    safe_resource_paths = github_import_data.get("safe_resource_paths") or []
    risky_resource_paths = github_import_data.get("risky_resource_paths") or []

    if import_type == "manifest_skill":
        if "workflow" in content_preview or "n8n" in content_preview:
            return "workflow_skill"
        if risky_resource_paths:
            return "tool_skill"
        if safe_resource_paths:
            return "knowledge_skill"
        return "prompt_skill"

    if import_type == "markdown_instruction":
        if risky_resource_paths:
            return "tool_skill"
        if safe_resource_paths:
            if "workflow" in content_preview or any("workflow" in path.lower() for path in resource_paths):
                return "workflow_skill"
            return "knowledge_skill"
        if "workflow" in content_preview or "automation" in content_preview:
            return "workflow_skill"
        return "prompt_skill"

    return "prompt_skill"


def _clean_text(value) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def _extract_skill_title(skill) -> str:
    for field_name in ("name", "title", "slug"):
        candidate = _clean_text(getattr(skill, field_name, None))
        if candidate:
            return candidate

    skill_id = getattr(skill, "id", None)
    return str(skill_id) if skill_id is not None else "Unknown skill"


def _extract_skill_content(skill) -> str:
    for field_name in ("content", "instruction_text", "prompt", "text"):
        candidate = _clean_text(getattr(skill, field_name, None))
        if candidate:
            return candidate
    return ""


def _load_active_skill_context_entries(db: Session, *, agent_id: uuid.UUID) -> tuple[list[dict], list[str]]:
    assignments = agent_skill_repository.list_agent_skills(db, agent_id)
    entries: list[dict] = []
    warnings: list[str] = []

    for assignment in assignments:
        skill = assignment.skill
        if not assignment.is_enabled or skill is None:
            continue
        if skill.deleted_at is not None or skill.status != "active":
            continue

        github_import_data = _load_github_import_data(db, skill)
        skill_type = _infer_skill_type(skill, github_import_data)
        if skill_type not in {"prompt_skill", "knowledge_skill"}:
            continue

        title = _extract_skill_title(skill)
        content = _extract_skill_content(skill)
        if not content:
            warnings.append(f"Skipped {skill_type.replace('_', ' ')} '{title}' because it has no usable content.")
            continue

        created_at = getattr(assignment, "created_at", None) or datetime.min.replace(tzinfo=UTC)
        entries.append(
            {
                "created_at": created_at,
                "title": title,
                "skill_id": str(skill.id),
                "content": content,
                "skill_type": skill_type,
            }
        )

    entries.sort(key=lambda item: (item["created_at"], item["title"].lower(), item["skill_id"]))
    return entries, warnings


def _compile_prompt_system_prompt(entries: list[dict]) -> tuple[str, list[str]]:
    prompt_entries = [entry for entry in entries if entry["skill_type"] == "prompt_skill"]
    compiled_contents = [entry["content"] for entry in prompt_entries]
    prompt_skills_used = [entry["title"] for entry in prompt_entries]
    system_prompt = "\n\n".join(compiled_contents) if compiled_contents else CHAT_DEFAULT_SYSTEM_PROMPT
    return system_prompt, prompt_skills_used


def _build_knowledge_context(entries: list[dict]) -> tuple[str, list[str], bool]:
    knowledge_entries = [entry for entry in entries if entry["skill_type"] == "knowledge_skill"]
    if not knowledge_entries:
        return "", [], False

    wrapper_overhead = (
        len(CHAT_KNOWLEDGE_CONTEXT_HEADER)
        + len(CHAT_KNOWLEDGE_CONTEXT_FOOTER)
        + len("\n")
        + len("\n")
    )
    available_body_chars = max(0, CHAT_KNOWLEDGE_CONTEXT_CHAR_LIMIT - wrapper_overhead)
    rendered_parts: list[str] = []
    knowledge_skills_used: list[str] = []
    remaining = available_body_chars
    truncated = False

    for entry in knowledge_entries:
        separator = "\n\n" if rendered_parts else ""
        title_block = f"[{entry['title']}]\n"
        entry_length = len(separator) + len(title_block)

        if remaining <= entry_length:
            truncated = True
            break

        if separator:
            rendered_parts.append(separator)
            remaining -= len(separator)

        rendered_parts.append(title_block)
        remaining -= len(title_block)

        content = entry["content"]
        if len(content) <= remaining:
            rendered_parts.append(content)
            remaining -= len(content)
            knowledge_skills_used.append(entry["title"])
            continue

        rendered_parts.append(content[:remaining])
        knowledge_skills_used.append(entry["title"])
        truncated = True
        remaining = 0
        break

    body = "".join(rendered_parts).strip()
    if not body:
        return "", [], False

    return f"{CHAT_KNOWLEDGE_CONTEXT_HEADER}\n{body}\n{CHAT_KNOWLEDGE_CONTEXT_FOOTER}", knowledge_skills_used, truncated


def _post_json(url: str, headers: dict[str, str], body: dict, timeout: float) -> tuple[int, str]:
    request = Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
        return response.status, raw


def _extract_text_from_content(content) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    texts.append(text.strip())
        return "\n".join(texts).strip()

    if isinstance(content, dict):
        text = content.get("text")
        if isinstance(text, str):
            return text.strip()

    return ""


def _chat_openai_or_openrouter(*, url: str, api_key: str, model: str, system_prompt: str, messages: list[dict]) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if "openrouter.ai" in url:
        headers.update(
            {
                "HTTP-Referer": "http://localhost",
                "X-Title": "Personal AI Agent Workspace",
            }
        )

    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
        "temperature": 0.2,
    }

    try:
        _, raw_response = _post_json(url, headers, payload, timeout=30.0)
        data = json.loads(raw_response)
        choices = data.get("choices") or []
        if not choices:
            raise AgentChatUnauthorizedError()

        message = choices[0].get("message") or {}
        reply = _extract_text_from_content(message.get("content"))
        if not reply:
            raise AgentChatUnauthorizedError()

        usage = data.get("usage") or {}
        return {
            "reply": reply,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
        }
    except (HTTPError, URLError, ValueError, KeyError, IndexError, TypeError):
        raise AgentChatUnauthorizedError()


def _chat_anthropic(*, api_key: str, model: str, system_prompt: str, messages: list[dict]) -> dict:
    payload = {
        "model": model,
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": messages,
        "temperature": 0.2,
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    try:
        _, raw_response = _post_json("https://api.anthropic.com/v1/messages", headers, payload, timeout=30.0)
        data = json.loads(raw_response)
        reply = _extract_text_from_content(data.get("content"))
        if not reply:
            raise AgentChatUnauthorizedError()

        usage = data.get("usage") or {}
        return {
            "reply": reply,
            "prompt_tokens": usage.get("input_tokens"),
            "completion_tokens": usage.get("output_tokens"),
        }
    except (HTTPError, URLError, ValueError, KeyError, IndexError, TypeError):
        raise AgentChatUnauthorizedError()


def _chat_gemini(*, api_key: str, model: str, system_prompt: str, messages: list[dict]) -> dict:
    normalized_messages = []
    for message in messages:
        role = "model" if message.get("role") == "assistant" else "user"
        normalized_messages.append(
            {
                "role": role,
                "parts": [{"text": message.get("content", "")}],
            }
        )

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": normalized_messages,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        },
    }
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )

    try:
        _, raw_response = _post_json(url, {"Content-Type": "application/json"}, payload, timeout=30.0)
        data = json.loads(raw_response)
        candidates = data.get("candidates") or []
        if not candidates:
            raise AgentChatUnauthorizedError()

        content = candidates[0].get("content") or {}
        reply = _extract_text_from_content(content.get("parts"))
        if not reply:
            raise AgentChatUnauthorizedError()

        usage = data.get("usageMetadata") or {}
        return {
            "reply": reply,
            "prompt_tokens": usage.get("promptTokenCount"),
            "completion_tokens": usage.get("candidatesTokenCount"),
        }
    except (HTTPError, URLError, ValueError, KeyError, IndexError, TypeError):
        raise AgentChatUnauthorizedError()


def call_provider_chat_completion(
    *,
    provider: str,
    api_key: str,
    model: str,
    system_prompt: str,
    messages: list[dict],
) -> dict:
    normalized_provider = normalize_provider_id(provider)
    if normalized_provider == MODEL_PROVIDER_OPENAI:
        return _chat_openai_or_openrouter(
            url="https://api.openai.com/v1/chat/completions",
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            messages=messages,
        )
    if normalized_provider == MODEL_PROVIDER_OPENROUTER:
        return _chat_openai_or_openrouter(
            url="https://openrouter.ai/api/v1/chat/completions",
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            messages=messages,
        )
    if normalized_provider == MODEL_PROVIDER_ANTHROPIC:
        return _chat_anthropic(
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            messages=messages,
        )
    if normalized_provider == MODEL_PROVIDER_GOOGLE_GEMINI:
        return _chat_gemini(
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            messages=messages,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=CHAT_UNSUPPORTED_PROVIDER_MESSAGE,
    )


def _log_chat_attempt(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    provider: str,
    model: str,
    success: bool,
    prompt_skill_count: int,
    knowledge_skill_count: int,
    knowledge_truncated: bool,
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> None:
    log_service.record_activity(
        db,
        actor_type="user",
        actor_id=owner_id,
        request_id=None,
        event_type="agent.chat",
        message="Agent chat completed." if success else "Agent chat failed.",
        metadata_json={
            "user_id": str(owner_id),
            "agent_id": str(agent_id),
            "session_id": str(session_id) if session_id is not None else None,
            "provider": provider,
            "model": model,
            "success": success,
            "prompt_skill_count": prompt_skill_count,
            "knowledge_skill_count": knowledge_skill_count,
            "knowledge_truncated": knowledge_truncated,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
    )
    db.commit()


def chat_with_agent(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    payload: AgentChatRequest,
    current_user=None,
) -> AgentChatResponse:
    _rate_limit_bucket(owner_id)
    agent = _resolve_agent_for_chat(db, owner_id=owner_id, agent_id=agent_id, current_user=current_user)
    existing_session = None
    if payload.session_id is not None:
        existing_session = session_service.load_session_for_owner(
            db,
            user_id=owner_id,
            session_id=payload.session_id,
        )
        if existing_session.session_type != session_service.SESSION_TYPE_AGENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session type mismatch.",
            )
        if existing_session.agent_id != agent.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session does not belong to this agent.",
            )

    normalized_messages = [message.model_dump() for message in payload.messages]
    active_skill_entries, warnings = _load_active_skill_context_entries(db, agent_id=agent.id)
    system_prompt, prompt_skills_used = _compile_prompt_system_prompt(active_skill_entries)
    knowledge_context, knowledge_skills_used, knowledge_truncated = _build_knowledge_context(
        active_skill_entries
    )
    response_warnings = list(warnings)
    if knowledge_truncated:
        response_warnings.append("Knowledge context truncated due to length limit")
    if knowledge_context:
        system_prompt = f"{system_prompt}\n\n{knowledge_context}"
    provider, model = _load_provider_configuration(db, owner_id=owner_id)

    api_key_record = model_provider_api_key_repository.get_by_owner_and_provider(db, owner_id, provider)
    if api_key_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=CHAT_NO_API_KEY_MESSAGE,
        )

    try:
        api_key = decrypt_api_key(api_key_record.encrypted_api_key)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=CHAT_NO_API_KEY_MESSAGE,
        )

    try:
        provider_result = call_provider_chat_completion(
            provider=provider,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            messages=normalized_messages,
        )
        reply = str(provider_result.get("reply") or "").strip()
        if not reply:
            raise AgentChatUnauthorizedError()

        session_record = session_service.upsert_chat_session(
            db,
            user_id=owner_id,
            session_type=session_service.SESSION_TYPE_AGENT,
            messages=normalized_messages,
            assistant_reply=reply,
            agent_id=agent.id,
            session_id=existing_session.id if existing_session is not None else None,
        )
        prompt_tokens = provider_result.get("prompt_tokens")
        completion_tokens = provider_result.get("completion_tokens")
        _log_chat_attempt(
            db,
            owner_id=owner_id,
            agent_id=agent.id,
            session_id=session_record.id,
            provider=provider,
            model=model,
            success=True,
            prompt_skill_count=len(prompt_skills_used),
            knowledge_skill_count=len(knowledge_skills_used),
            knowledge_truncated=knowledge_truncated,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        return AgentChatResponse(
            session_id=session_record.id,
            agent_id=str(agent.id),
            agent_name=agent.name,
            reply=reply,
            provider=provider,
            model=model,
            prompt_skills_used=prompt_skills_used,
            knowledge_skills_used=knowledge_skills_used,
            knowledge_truncated=knowledge_truncated,
            warning="; ".join(response_warnings) if response_warnings else None,
        )
    except AgentChatUnauthorizedError:
        _log_chat_attempt(
            db,
            owner_id=owner_id,
            agent_id=agent.id,
            session_id=None,
            provider=provider,
            model=model,
            success=False,
            prompt_skill_count=len(prompt_skills_used),
            knowledge_skill_count=len(knowledge_skills_used),
            knowledge_truncated=knowledge_truncated,
            prompt_tokens=None,
            completion_tokens=None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=CHAT_UNAUTHORIZED_MESSAGE,
        )
    except HTTPException:
        raise
    except Exception:
        _log_chat_attempt(
            db,
            owner_id=owner_id,
            agent_id=agent.id,
            session_id=None,
            provider=provider,
            model=model,
            success=False,
            prompt_skill_count=len(prompt_skills_used),
            knowledge_skill_count=len(knowledge_skills_used),
            knowledge_truncated=knowledge_truncated,
            prompt_tokens=None,
            completion_tokens=None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=CHAT_UNAUTHORIZED_MESSAGE,
        )
