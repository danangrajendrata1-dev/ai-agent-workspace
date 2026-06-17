import httpx
from unittest.mock import MagicMock, patch

from app.core.workflow_webhook_client import WebhookCallResult, call_template_webhook


class _FakeResponse:
    def __init__(self, *, status_code: int, body: bytes, content_type: str = "application/json"):
        self.status_code = status_code
        self.headers = {"content-type": content_type}
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def iter_bytes(self):
        yield self._body


class _FakeClient:
    def __init__(self, response: _FakeResponse | None = None, exception: Exception | None = None):
        self.response = response
        self.exception = exception
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def stream(self, method, url, json=None):
        self.calls.append({"method": method, "url": url, "json": json})
        if self.exception is not None:
            raise self.exception
        return self.response


def test_call_template_webhook_uses_safe_http_settings_and_sanitizes_output():
    fake_client = _FakeClient(
        response=_FakeResponse(
            status_code=200,
            body=b'{"ok":true,"message":"done"}',
        )
    )
    client_cls = MagicMock(return_value=fake_client)

    with patch("app.core.workflow_webhook_client.httpx.Client", client_cls):
        result = call_template_webhook(
            "https://workflow.example.org/webhook/generate-pdf",
            {"title": "Hello", "content": "World"},
        )

    assert result.success is True
    assert result.status_code == 200
    assert result.response_summary == "Webhook completed successfully."
    assert result.response_truncated is False
    assert client_cls.call_args.kwargs["follow_redirects"] is False
    assert client_cls.call_args.kwargs["trust_env"] is False
    assert fake_client.calls == [
        {
            "method": "POST",
            "url": "https://workflow.example.org/webhook/generate-pdf",
            "json": {"title": "Hello", "content": "World"},
        }
    ]


def test_call_template_webhook_timeout_returns_safe_result():
    request = httpx.Request("POST", "https://workflow.example.org/webhook/generate-pdf")
    timeout_error = httpx.ReadTimeout("timed out", request=request)
    client_cls = MagicMock(return_value=_FakeClient(exception=timeout_error))

    with patch("app.core.workflow_webhook_client.httpx.Client", client_cls):
        result = call_template_webhook(
            "https://workflow.example.org/webhook/generate-pdf",
            {"title": "Hello"},
        )

    assert result == WebhookCallResult(
        success=False,
        status_code=None,
        response_summary=None,
        error_message="Webhook request timed out.",
        timed_out=True,
        response_truncated=False,
    )


def test_call_template_webhook_truncates_large_response_summary():
    large_body = b"a" * (1024 * 1024 + 4096)
    fake_client = _FakeClient(
        response=_FakeResponse(
            status_code=500,
            body=large_body,
            content_type="text/plain",
        )
    )
    client_cls = MagicMock(return_value=fake_client)

    with patch("app.core.workflow_webhook_client.httpx.Client", client_cls):
        result = call_template_webhook(
            "https://workflow.example.org/webhook/generate-pdf",
            {"title": "Hello"},
        )

    assert result.success is False
    assert result.status_code == 500
    assert result.response_truncated is True
    assert result.error_message == "Webhook returned HTTP 500."
    assert result.response_summary == "Webhook returned HTTP 500."
