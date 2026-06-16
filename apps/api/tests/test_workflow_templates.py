import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core import workflow_templates
from app.services.workflow_service import clear_workflow_rate_limiter

from .test_sessions import auth_headers


@pytest.fixture(autouse=True)
def reset_workflow_rate_limiter():
    clear_workflow_rate_limiter()


def test_workflow_templates_list_requires_authentication(client):
    response = client.get("/workflows/templates")

    assert response.status_code == 401


def test_workflow_templates_list_returns_safe_fields(client):
    user_id = uuid.uuid4()
    with patch("app.services.auth_service.get_current_active_user", return_value=SimpleNamespace(id=user_id, role="user")):
        response = client.get("/workflows/templates", headers=auth_headers(user_id))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    template = payload["items"][0]
    assert template["id"] == "generate_pdf"
    assert template["enabled"] is False
    assert template["consented"] is False
    assert "webhook_url" not in template
    assert template["input_schema"] == {"title": "string", "content": "string"}


def test_disabled_template_cannot_be_consented(client):
    user_id = uuid.uuid4()
    with patch("app.services.auth_service.get_current_active_user", return_value=SimpleNamespace(id=user_id, role="user")):
        response = client.post("/workflows/consent/generate_pdf", headers=auth_headers(user_id))

    assert response.status_code == 400
    assert "disabled" in response.json()["detail"].lower()


def test_missing_template_cannot_be_consented(client):
    user_id = uuid.uuid4()
    with patch("app.services.auth_service.get_current_active_user", return_value=SimpleNamespace(id=user_id, role="user")):
        response = client.post("/workflows/consent/missing_template", headers=auth_headers(user_id))

    assert response.status_code == 404


def test_validate_workflow_templates_accepts_enabled_safe_template(monkeypatch):
    monkeypatch.setattr(
        workflow_templates,
        "WORKFLOW_TEMPLATES",
        {
            "enable_test": {
                "id": "enable_test",
                "name": "Enabled Template",
                "description": "Safe enabled template",
                "webhook_url": "https://workflow.example.org/webhook",
                "input_schema": {"title": "string"},
                "output_type": "json",
                "enabled": True,
                "template_version": "1.0",
                "risk_level": "medium",
                "max_payload_bytes": 1000,
            }
        },
    )
    monkeypatch.setattr(
        workflow_templates,
        "validate_safe_webhook_url",
        lambda url: (True, None),
    )

    assert workflow_templates.validate_workflow_templates() == []


def test_validate_workflow_templates_rejects_invalid_enabled_template(monkeypatch):
    monkeypatch.setattr(
        workflow_templates,
        "WORKFLOW_TEMPLATES",
        {
            "bad_template": {
                "id": "bad_template",
                "name": "Bad Template",
                "description": "Invalid enabled template",
                "webhook_url": "https://workflow.example.org/webhook",
                "input_schema": {"title": "string"},
                "output_type": "json",
                "enabled": True,
                "template_version": "1.0",
                "risk_level": "medium",
                "max_payload_bytes": 1000,
            }
        },
    )
    monkeypatch.setattr(
        workflow_templates,
        "validate_safe_webhook_url",
        lambda url: (False, "DNS resolution failed."),
    )

    errors = workflow_templates.validate_workflow_templates()

    assert errors
    assert any("dns resolution failed" in error.lower() or "unsafe webhook url" in error.lower() for error in errors)
