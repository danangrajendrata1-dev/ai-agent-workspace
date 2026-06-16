from __future__ import annotations

import ipaddress
import json
import socket
from urllib.parse import urlsplit, urlunsplit


_BLOCKED_HOSTS = {"metadata.google.internal"}
_BLOCKED_SECRET_KEYS = {"token", "secret", "password", "api_key", "authorization", "credential", "cookie"}


def canonicalize_webhook_url(url: str) -> str:
    parsed = urlsplit(str(url).strip())
    scheme = parsed.scheme.lower()
    hostname = parsed.hostname.lower() if parsed.hostname else ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = hostname + port
    return urlunsplit((scheme, netloc, parsed.path or "", parsed.query or "", ""))


def _is_blocked_ip(value: str) -> bool:
    ip = ipaddress.ip_address(value)
    return any(
        [
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        ]
    ) or (ip.version == 6 and ip in ipaddress.ip_network("fc00::/7"))


def _validate_host(hostname: str) -> tuple[bool, str | None]:
    host = hostname.lower().strip()
    if not host:
        return False, "Webhook host is required."
    if host in _BLOCKED_HOSTS:
        return False, "Blocked internal hostname."
    if host == "localhost" or host.endswith(".localhost"):
        return False, "Localhost is not allowed."
    if host.endswith(".local"):
        return False, "Local network hostnames are not allowed."

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None

    if ip is not None:
        if _is_blocked_ip(host):
            return False, "Private or internal IP addresses are not allowed."
        return True, None

    try:
        resolved = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False, "DNS resolution failed."

    if not resolved:
        return False, "DNS resolution failed."

    for item in resolved:
        address = item[4][0]
        try:
            if _is_blocked_ip(address):
                return False, "DNS resolved to a private or internal IP address."
        except ValueError:
            return False, "DNS resolved to an invalid IP address."

    return True, None


def validate_safe_webhook_url(url: str) -> tuple[bool, str | None]:
    if not isinstance(url, str) or not url.strip():
        return False, "Webhook URL is required."

    parsed = urlsplit(url.strip())
    if parsed.scheme.lower() != "https":
        return False, "Webhook URL must use HTTPS."
    if not parsed.hostname:
        return False, "Webhook host is required."
    if parsed.username or parsed.password:
        return False, "Webhook URL must not include credentials."
    if parsed.fragment:
        return False, "Webhook URL must not include a fragment."

    canonical_url = canonicalize_webhook_url(url)
    canonical_parsed = urlsplit(canonical_url)
    if canonical_parsed.scheme.lower() != "https":
        return False, "Webhook URL must use HTTPS."

    return _validate_host(canonical_parsed.hostname or "")


def sanitize_payload_for_template(template: dict, input_payload: dict | None) -> dict:
    if not isinstance(template, dict) or not isinstance(input_payload, dict):
        return {}

    input_schema = template.get("input_schema") or {}
    if not isinstance(input_schema, dict):
        return {}

    max_payload_bytes = int(template.get("max_payload_bytes") or 0)
    allowed_keys = list(input_schema.keys())
    sanitized: dict[str, object] = {}

    for key in allowed_keys:
        if not isinstance(key, str):
            continue
        if key not in input_payload:
            continue

        lowered_key = key.lower()
        if any(secret_key in lowered_key for secret_key in _BLOCKED_SECRET_KEYS):
            continue

        value = input_payload[key]
        if isinstance(value, str):
            cleaned = " ".join(value.split())
            if cleaned:
                sanitized[key] = cleaned
            continue

        if isinstance(value, (int, float, bool)) or value is None:
            sanitized[key] = value
            continue

        try:
            sanitized[key] = json.loads(json.dumps(value))
        except (TypeError, ValueError):
            continue

    if max_payload_bytes <= 0:
        return sanitized

    encoded = json.dumps(sanitized, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) <= max_payload_bytes:
        return sanitized

    trimmed = dict(sanitized)
    string_keys = [key for key, value in trimmed.items() if isinstance(value, str)]
    for key in sorted(string_keys, key=lambda item: len(str(trimmed[item])), reverse=True):
        current_value = str(trimmed[key])
        overflow = len(
            json.dumps(trimmed, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ) - max_payload_bytes
        if overflow <= 0:
            break
        if len(current_value) <= 8:
            trimmed.pop(key, None)
            continue
        cut_length = max(1, len(current_value) - overflow - 3)
        trimmed[key] = current_value[:cut_length].rstrip() + "..."

    final_encoded = json.dumps(trimmed, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(final_encoded) > max_payload_bytes:
        raise ValueError("Sanitized payload exceeds maximum size for template.")
    return trimmed


def sanitize_error_message(error) -> str:
    if error is None:
        return "Unknown error."

    if isinstance(error, Exception):
        message = str(error)
    else:
        message = str(error)

    cleaned = " ".join(message.split())
    lowered = cleaned.lower()
    if any(secret_key in lowered for secret_key in _BLOCKED_SECRET_KEYS):
        return "Sensitive error redacted."
    if len(cleaned) > 500:
        cleaned = cleaned[:500].rstrip() + "..."
    return cleaned or "Unknown error."
