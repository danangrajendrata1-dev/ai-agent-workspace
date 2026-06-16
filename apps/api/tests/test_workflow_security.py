import socket
from unittest.mock import patch

from app.core.webhook_security import (
    canonicalize_webhook_url,
    sanitize_error_message,
    sanitize_payload_for_template,
    validate_safe_webhook_url,
)


def test_canonicalize_webhook_url_strips_fragment_and_normalizes_host():
    assert canonicalize_webhook_url("HTTPS://Example.COM:443/path?q=1#frag") == "https://example.com:443/path?q=1"


def test_validate_safe_webhook_url_rejects_insecure_and_internal_hosts():
    assert validate_safe_webhook_url("http://example.com/webhook")[0] is False
    assert validate_safe_webhook_url("https://localhost/webhook")[0] is False
    assert validate_safe_webhook_url("https://service.local/webhook")[0] is False
    assert validate_safe_webhook_url("https://metadata.google.internal/webhook")[0] is False
    assert validate_safe_webhook_url("https://127.0.0.1/webhook")[0] is False
    assert validate_safe_webhook_url("https://[::1]/webhook")[0] is False
    assert validate_safe_webhook_url("https://user:pass@example.com/webhook")[0] is False


def test_validate_safe_webhook_url_rejects_dns_private_resolution():
    fake_result = [
        (
            socket.AF_INET,
            socket.SOCK_STREAM,
            6,
            "",
            ("10.0.0.8", 443),
        )
    ]

    with patch("socket.getaddrinfo", return_value=fake_result):
        is_safe, reason = validate_safe_webhook_url("https://workflow.example.test/webhook")

    assert is_safe is False
    assert "private or internal IP" in (reason or "")


def test_sanitize_payload_for_template_allows_only_schema_fields_and_drops_secrets():
    template = {
        "input_schema": {
            "title": "string",
            "content": "string",
            "token": "string",
        },
        "max_payload_bytes": 1000,
    }
    payload = {
        "title": "  Hello   World  ",
        "content": "  Keep   this  ",
        "token": "secret-value",
        "api_key": "another-secret",
        "extra": "drop me",
    }

    sanitized = sanitize_payload_for_template(template, payload)

    assert sanitized == {
        "title": "Hello World",
        "content": "Keep this",
    }


def test_sanitize_error_message_redacts_secret_like_content():
    assert sanitize_error_message("token leaked in error") == "Sensitive error redacted."
