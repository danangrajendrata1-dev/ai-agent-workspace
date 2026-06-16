from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.provider_api_keys import decrypt_api_key, validate_api_key_provider
from app.core.provider_settings import (
    MODEL_PROVIDER_ANTHROPIC,
    MODEL_PROVIDER_GOOGLE_GEMINI,
    MODEL_PROVIDER_OPENAI,
    MODEL_PROVIDER_OPENROUTER,
    MODEL_PROVIDER_CUSTOM,
)
from app.repositories import model_provider_api_key_repository
from app.schemas.model_provider_api_key import ProviderTestResponse


RATE_LIMIT_MAX_REQUESTS = 5
RATE_LIMIT_WINDOW_SECONDS = 60
SAFE_NO_KEY_MESSAGE = "No API key found for this provider"
SAFE_NOT_INTEGRATED_MESSAGE = "Provider not yet integrated"
SAFE_UNAUTHORIZED_MESSAGE = "Invalid API key or unauthorized"
SAFE_SUCCESS_MESSAGE = "Connection successful"
SAFE_RATE_LIMIT_MESSAGE = "Too many attempts. Try again later."
SUPPORTED_TEST_PROVIDERS = {
    MODEL_PROVIDER_OPENAI,
    MODEL_PROVIDER_ANTHROPIC,
    MODEL_PROVIDER_GOOGLE_GEMINI,
    MODEL_PROVIDER_OPENROUTER,
    MODEL_PROVIDER_CUSTOM,
}
INTEGRATED_TEST_PROVIDERS = {
    MODEL_PROVIDER_OPENAI,
    MODEL_PROVIDER_ANTHROPIC,
    MODEL_PROVIDER_GOOGLE_GEMINI,
}
TEST_PROMPT = "Say: connection ok"
TEST_MODEL_OPENAI = "gpt-4o-mini"
TEST_MODEL_ANTHROPIC = "claude-3-5-haiku-latest"
TEST_MODEL_GEMINI = "gemini-1.5-flash"
TEST_MODEL_OPENROUTER = "openai/gpt-4o-mini"


@dataclass(slots=True)
class ProviderConnectionProbeResult:
    success: bool


class ProviderConnectionUnauthorizedError(RuntimeError):
    pass


class ProviderConnectionNotIntegratedError(RuntimeError):
    pass


_rate_limit_lock = threading.Lock()
_rate_limit_state: dict[str, list[float]] = {}


def clear_provider_test_rate_limiter() -> None:
    with _rate_limit_lock:
        _rate_limit_state.clear()


def _rate_limit_bucket(owner_id: uuid.UUID) -> list[float]:
    now = time.monotonic()
    with _rate_limit_lock:
        bucket = _rate_limit_state.setdefault(str(owner_id), [])
        bucket[:] = [timestamp for timestamp in bucket if now - timestamp < RATE_LIMIT_WINDOW_SECONDS]
        if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=SAFE_RATE_LIMIT_MESSAGE,
            )
        bucket.append(now)
        return bucket


def _load_provider_api_key(db: Session, *, owner_id: uuid.UUID, provider: str) -> str | None:
    record = model_provider_api_key_repository.get_by_owner_and_provider(db, owner_id, provider)
    if record is None:
        return None

    try:
        return decrypt_api_key(record.encrypted_api_key)
    except HTTPException:
        return None
    except Exception:
        return None


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


def _test_openai(api_key: str) -> ProviderConnectionProbeResult:
    status_code, _ = _post_json(
        "https://api.openai.com/v1/chat/completions",
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        {
            "model": TEST_MODEL_OPENAI,
            "messages": [{"role": "user", "content": TEST_PROMPT}],
            "max_tokens": 10,
            "temperature": 0,
        },
        timeout=10.0,
    )
    if 200 <= status_code < 300:
        return ProviderConnectionProbeResult(success=True)
    raise ProviderConnectionUnauthorizedError()


def _test_anthropic(api_key: str) -> ProviderConnectionProbeResult:
    status_code, _ = _post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        {
            "model": TEST_MODEL_ANTHROPIC,
            "max_tokens": 10,
            "messages": [{"role": "user", "content": TEST_PROMPT}],
        },
        timeout=10.0,
    )
    if 200 <= status_code < 300:
        return ProviderConnectionProbeResult(success=True)
    raise ProviderConnectionUnauthorizedError()


def _test_gemini(api_key: str) -> ProviderConnectionProbeResult:
    base_url = "https://generativelanguage.googleapis.com/v1beta/models/"
    url = f"{base_url}{TEST_MODEL_GEMINI}:generateContent?{urlencode({'key': api_key})}"
    status_code, _ = _post_json(
        url,
        {"Content-Type": "application/json"},
        {
            "contents": [{"parts": [{"text": TEST_PROMPT}]}],
            "generationConfig": {"maxOutputTokens": 10, "temperature": 0},
        },
        timeout=10.0,
    )
    if 200 <= status_code < 300:
        return ProviderConnectionProbeResult(success=True)
    raise ProviderConnectionUnauthorizedError()


def _test_openrouter(api_key: str) -> ProviderConnectionProbeResult:
    status_code, _ = _post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Personal AI Agent Workspace",
        },
        {
            "model": TEST_MODEL_OPENROUTER,
            "messages": [{"role": "user", "content": TEST_PROMPT}],
            "max_tokens": 10,
            "temperature": 0,
        },
        timeout=10.0,
    )
    if 200 <= status_code < 300:
        return ProviderConnectionProbeResult(success=True)
    raise ProviderConnectionUnauthorizedError()


def build_provider_connection_probe(provider: str) -> Callable[[str], ProviderConnectionProbeResult]:
    normalized_provider = validate_api_key_provider(provider)
    if normalized_provider not in SUPPORTED_TEST_PROVIDERS:
        raise ProviderConnectionNotIntegratedError()
    if normalized_provider == MODEL_PROVIDER_CUSTOM:
        raise ProviderConnectionNotIntegratedError()
    if normalized_provider == MODEL_PROVIDER_OPENAI:
        return _test_openai
    if normalized_provider == MODEL_PROVIDER_ANTHROPIC:
        return _test_anthropic
    if normalized_provider == MODEL_PROVIDER_GOOGLE_GEMINI:
        return _test_gemini
    if normalized_provider == MODEL_PROVIDER_OPENROUTER:
        return _test_openrouter
    raise ProviderConnectionNotIntegratedError()


def test_provider_connection(
    db: Session,
    *,
    owner_id: uuid.UUID,
    provider: str,
) -> ProviderTestResponse:
    normalized_provider = validate_api_key_provider(provider)
    _rate_limit_bucket(owner_id)

    try:
        probe = build_provider_connection_probe(normalized_provider)
    except ProviderConnectionNotIntegratedError:
        return ProviderTestResponse(
            success=False,
            provider=normalized_provider,
            message=SAFE_NOT_INTEGRATED_MESSAGE,
        )

    api_key = _load_provider_api_key(db, owner_id=owner_id, provider=normalized_provider)
    if api_key is None:
        return ProviderTestResponse(
            success=False,
            provider=normalized_provider,
            message=SAFE_NO_KEY_MESSAGE,
        )

    try:
        probe_result = probe(api_key)
        if probe_result.success:
            return ProviderTestResponse(
                success=True,
                provider=normalized_provider,
                message=SAFE_SUCCESS_MESSAGE,
            )
        return ProviderTestResponse(
            success=False,
            provider=normalized_provider,
            message=SAFE_UNAUTHORIZED_MESSAGE,
        )
    except ProviderConnectionUnauthorizedError:
        return ProviderTestResponse(
            success=False,
            provider=normalized_provider,
            message=SAFE_UNAUTHORIZED_MESSAGE,
        )
    except HTTPError as exc:
        if exc.code in {401, 403}:
            return ProviderTestResponse(
                success=False,
                provider=normalized_provider,
                message=SAFE_UNAUTHORIZED_MESSAGE,
            )
        return ProviderTestResponse(
            success=False,
            provider=normalized_provider,
            message=SAFE_UNAUTHORIZED_MESSAGE,
        )
    except URLError:
        return ProviderTestResponse(
            success=False,
            provider=normalized_provider,
            message=SAFE_UNAUTHORIZED_MESSAGE,
        )
    except Exception:
        return ProviderTestResponse(
            success=False,
            provider=normalized_provider,
            message=SAFE_UNAUTHORIZED_MESSAGE,
        )
