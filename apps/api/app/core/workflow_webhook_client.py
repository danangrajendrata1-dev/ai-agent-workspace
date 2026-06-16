from __future__ import annotations

from dataclasses import dataclass
import json

import httpx

from app.core.webhook_security import sanitize_error_message


MAX_WEBHOOK_RESPONSE_BYTES = 1024 * 1024
MAX_WEBHOOK_RESPONSE_SUMMARY_CHARS = 500


@dataclass(frozen=True, slots=True)
class WebhookCallResult:
    success: bool
    status_code: int | None
    response_summary: str | None
    error_message: str | None
    timed_out: bool = False
    response_truncated: bool = False


def _summarize_response_bytes(response_bytes: bytes, content_type: str | None) -> str | None:
    if not response_bytes:
        return None

    decoded = response_bytes.decode("utf-8", errors="replace").strip()
    if not decoded:
        return None

    content_type_value = (content_type or "").lower()
    if "application/json" in content_type_value:
        try:
            payload = json.loads(decoded)
            decoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    if len(decoded) > MAX_WEBHOOK_RESPONSE_SUMMARY_CHARS:
        suffix = "..."
        decoded = decoded[: MAX_WEBHOOK_RESPONSE_SUMMARY_CHARS - len(suffix)].rstrip() + suffix
    return decoded


def call_template_webhook(url: str, payload: dict, timeout_seconds: int = 10) -> WebhookCallResult:
    timeout = httpx.Timeout(connect=5.0, read=float(timeout_seconds), write=10.0, pool=5.0)

    try:
        with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False) as client:
            with client.stream("POST", url, json=payload) as response:
                response_bytes = bytearray()
                truncated = False
                for chunk in response.iter_bytes():
                    if not chunk:
                        continue
                    remaining = MAX_WEBHOOK_RESPONSE_BYTES - len(response_bytes)
                    if remaining <= 0:
                        truncated = True
                        break
                    response_bytes.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        truncated = True
                        break

                summary = _summarize_response_bytes(bytes(response_bytes), response.headers.get("content-type"))
                return WebhookCallResult(
                    success=200 <= response.status_code < 300,
                    status_code=response.status_code,
                    response_summary=summary,
                    error_message=None if 200 <= response.status_code < 300 else f"Webhook returned HTTP {response.status_code}.",
                    timed_out=False,
                    response_truncated=truncated,
                )
    except httpx.TimeoutException:
        return WebhookCallResult(
            success=False,
            status_code=None,
            response_summary=None,
            error_message="Webhook request timed out.",
            timed_out=True,
            response_truncated=False,
        )
    except httpx.HTTPError as exc:
        return WebhookCallResult(
            success=False,
            status_code=None,
            response_summary=None,
            error_message=sanitize_error_message(exc),
            timed_out=False,
            response_truncated=False,
        )
