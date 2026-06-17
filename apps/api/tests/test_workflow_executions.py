import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.database import SessionLocal
from app.core.workflow_webhook_client import WebhookCallResult
from app.repositories import (
    agent_repository,
    skill_repository,
    workflow_consent_repository,
    workflow_execution_repository,
    workflow_skill_binding_repository,
)
from app.services.workflow_service import clear_workflow_rate_limiter

from .test_sessions import auth_headers, build_agent, build_user


@pytest.fixture(autouse=True)
def reset_workflow_rate_limiter():
    clear_workflow_rate_limiter()


def build_enabled_template(*, version: str = "1.0", webhook_url: str = "https://workflow.example.org/webhook/generate-pdf"):
    return {
        "id": "generate_pdf",
        "name": "Generate PDF",
        "description": "Membuat file PDF dari teks",
        "webhook_url": webhook_url,
        "input_schema": {"title": "string", "content": "string"},
        "output_type": "json",
        "enabled": True,
        "template_version": version,
        "risk_level": "medium",
        "max_payload_bytes": 10000,
    }


def build_workflow_skill_assignment(skill_id, *, skill_type: str = "workflow_skill", is_enabled: bool = True):
    skill_uuid = uuid.UUID(str(skill_id))
    return SimpleNamespace(
        skill_id=skill_uuid,
        skill=SimpleNamespace(title="Workflow Skill", type=skill_type, status="active"),
        is_enabled=is_enabled,
    )


def build_execution_context(
    *,
    user_prefix: str,
    template_version: str = "1.0",
    with_consent: bool = True,
    with_binding: bool = True,
):
    with SessionLocal() as db:
        user = build_user(db, email_prefix=user_prefix)
        agent = build_agent(db, owner_id=user.id, name=f"{user_prefix}-agent")
        skill = skill_repository.create(
            db,
            {
                "name": f"{user_prefix} Workflow Skill",
                "slug": f"{user_prefix}-workflow-skill-{uuid.uuid4().hex[:8]}",
                "description": "Workflow skill for execution tests.",
                "content": "Workflow skill content.",
                "source_type": "manual",
                "source_id": None,
                "version_label": "1.0",
                "risk_level": "medium",
                "status": "active",
            },
        )
        db.commit()
        db.refresh(skill)

        consent = None
        if with_consent:
            consent = workflow_consent_repository.create_consent(
                db,
                user_id=user.id,
                template_id="generate_pdf",
                template_version=template_version,
            )

        binding = None
        if with_binding:
            binding = workflow_skill_binding_repository.create_binding(
                db,
                user_id=user.id,
                skill_id=skill.id,
                template_id="generate_pdf",
                template_version=template_version,
            )

        db.commit()
        if consent is not None:
            db.refresh(consent)
        if binding is not None:
            db.refresh(binding)

        user_id = str(user.id)
        agent_id = str(agent.id)
        skill_id = str(skill.id)

    return SimpleNamespace(
        user=user,
        agent=agent,
        user_id=user_id,
        agent_id=agent_id,
        skill=skill,
        skill_id=skill_id,
        consent=consent,
        binding=binding,
    )


def test_execute_route_requires_authentication(client):
    response = client.post("/workflows/execute/generate_pdf", json={})

    assert response.status_code == 401


def test_execute_template_workflow_success_sanitizes_payload_and_saves_audit(client):
    context = build_execution_context(user_prefix="workflow-exec-success")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()
    webhook_result = WebhookCallResult(
        success=True,
        status_code=200,
        response_summary="Generated PDF queued.",
        error_message=None,
        timed_out=False,
        response_truncated=False,
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook",
        return_value=webhook_result,
    ) as mock_call, patch(
        "app.services.workflow_service.log_service.record_activity",
        return_value=None,
    ):
        response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {
                    "title": "  Monthly Report  ",
                    "content": "  Keep this safe  ",
                    "token": "secret-value",
                    "extra": "drop me",
                },
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["status"] == "success"
    assert payload["template_id"] == "generate_pdf"
    assert payload["template_version"] == "1.0"
    assert payload["output_summary"] == "Generated PDF queued."
    assert payload["error_message"] is None
    assert payload["http_status_code"] == 200
    assert payload["execution_id"] is not None
    mock_call.assert_called_once()
    called_url, called_payload = mock_call.call_args.args[:2]
    assert called_url == "https://workflow.example.org/webhook/generate-pdf"
    assert called_payload == {"title": "Monthly Report", "content": "Keep this safe"}

    with SessionLocal() as db:
        executions = workflow_execution_repository.list_executions(db, user_id=context.user.id)
        assert len(executions) == 1
        execution = executions[0]
        assert execution.status == "success"
        assert execution.webhook_url == "https://workflow.example.org/webhook/generate-pdf"
        assert execution.input_payload_sanitized == {"title": "Monthly Report", "content": "Keep this safe"}
        assert execution.output_summary == "Generated PDF queued."
        assert execution.error_message is None
        assert execution.http_status_code == 200


def test_chat_confirm_execute_template_workflow_success_sanitizes_payload_and_saves_audit(client):
    context = build_execution_context(user_prefix="workflow-chat-confirm-success")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()
    webhook_result = WebhookCallResult(
        success=True,
        status_code=200,
        response_summary='{"job":"queued"}',
        error_message=None,
        timed_out=False,
        response_truncated=False,
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook",
        return_value=webhook_result,
    ) as mock_call, patch(
        "app.services.workflow_service.log_service.record_activity",
        return_value=None,
    ):
        response = client.post(
            "/workflows/chat-confirm-execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {
                    "title": "  Monthly Report  ",
                    "content": "  Keep this safe  ",
                    "token": "secret-value",
                    "extra": "drop me",
                },
                "confirmed": True,
                "confirmation_source": "chat_suggestion",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["status"] == "success"
    assert payload["template_id"] == "generate_pdf"
    assert payload["template_version"] == "1.0"
    assert payload["output_summary"] == '{"job":"queued"}'
    assert payload["error_message"] is None
    assert payload["http_status_code"] == 200
    assert payload["execution_id"] is not None
    assert "raw_response" not in payload
    assert "response_body" not in payload
    mock_call.assert_called_once()
    called_url, called_payload = mock_call.call_args.args[:2]
    assert called_url == "https://workflow.example.org/webhook/generate-pdf"
    assert called_payload == {"title": "Monthly Report", "content": "Keep this safe"}

    with SessionLocal() as db:
        executions = workflow_execution_repository.list_executions(db, user_id=context.user.id)
        assert len(executions) == 1
        execution = executions[0]
        assert execution.status == "success"
        assert execution.webhook_url == "https://workflow.example.org/webhook/generate-pdf"
        assert execution.input_payload_sanitized == {"title": "Monthly Report", "content": "Keep this safe"}
        assert execution.output_summary == '{"job":"queued"}'
        assert execution.error_message is None
        assert execution.http_status_code == 200


def test_execute_requires_consent_before_webhook_call(client):
    context = build_execution_context(user_prefix="workflow-exec-consent", with_consent=False)
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_call:
        response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert response.status_code == 428
    payload = response.json()
    assert payload["status"] == "consent_required"
    assert payload["error_message"] == "Consent is required before this workflow can run."
    mock_call.assert_not_called()

    with SessionLocal() as db:
        executions = workflow_execution_repository.list_executions(db, user_id=context.user.id)
        assert executions == []


def test_execute_rejects_frontend_execution_available_field_without_call(client):
    context = build_execution_context(user_prefix="workflow-exec-frontend-flag", with_consent=False)
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_call:
        response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
                "execution_available": True,
            },
        )

    assert response.status_code == 428
    payload = response.json()
    assert payload["status"] == "consent_required"
    mock_call.assert_not_called()


def test_chat_confirm_execute_requires_consent_before_webhook_call(client):
    context = build_execution_context(user_prefix="workflow-chat-confirm-consent", with_consent=False)
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_call:
        response = client.post(
            "/workflows/chat-confirm-execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
                "confirmed": True,
                "confirmation_source": "chat_suggestion",
            },
        )

    assert response.status_code == 428
    payload = response.json()
    assert payload["status"] == "consent_required"
    assert payload["error_message"] == "Consent is required before this workflow can run."
    mock_call.assert_not_called()

    with SessionLocal() as db:
        executions = workflow_execution_repository.list_executions(db, user_id=context.user.id)
        assert executions == []


def test_chat_confirm_execute_rejects_frontend_execution_available_field_without_call(client):
    context = build_execution_context(user_prefix="workflow-chat-confirm-invalid")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_call:
        response = client.post(
            "/workflows/chat-confirm-execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
                "confirmed": True,
                "confirmation_source": "chat_suggestion",
                "execution_available": True,
            },
        )

    assert response.status_code == 422
    mock_call.assert_not_called()


def test_revoked_consent_blocks_future_execution_and_preserves_history(client):
    context = build_execution_context(user_prefix="workflow-exec-revoked")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()
    webhook_result = WebhookCallResult(
        success=True,
        status_code=200,
        response_summary="Generated PDF queued.",
        error_message=None,
        timed_out=False,
        response_truncated=False,
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook",
        return_value=webhook_result,
    ) as mock_call, patch(
        "app.services.workflow_service.log_service.record_activity",
        return_value=None,
    ):
        initial_response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert initial_response.status_code == 200
    assert initial_response.json()["status"] == "success"
    assert mock_call.call_count == 1

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_revoke_call:
        revoke_response = client.post(
            f"/workflows/consents/{context.consent.id}/revoke",
            headers=headers,
        )

    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"
    mock_revoke_call.assert_not_called()

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_execute_after_revoke:
        execute_after_revoke_response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert execute_after_revoke_response.status_code == 428
    assert execute_after_revoke_response.json()["status"] == "consent_required"
    mock_execute_after_revoke.assert_not_called()

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_chat_execute_after_revoke:
        chat_execute_after_revoke_response = client.post(
            "/workflows/chat-confirm-execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
                "confirmed": True,
                "confirmation_source": "chat_suggestion",
            },
        )

    assert chat_execute_after_revoke_response.status_code == 428
    assert chat_execute_after_revoke_response.json()["status"] == "consent_required"
    mock_chat_execute_after_revoke.assert_not_called()

    with SessionLocal() as db:
        executions = workflow_execution_repository.list_executions(db, user_id=context.user.id)
        assert len(executions) == 1
        history = workflow_execution_repository.list_executions(db, user_id=context.user.id)
        assert len(history) == 1


def test_workflow_execution_history_returns_only_current_user_items_and_sanitizes_fields(client):
    with SessionLocal() as db:
        user_one = build_user(db, email_prefix="workflow-history-one")
        user_two = build_user(db, email_prefix="workflow-history-two")
        base_time = datetime.now(UTC)
        workflow_execution_repository.create_execution(
            db,
            {
                "user_id": user_one.id,
                "agent_id": None,
                "skill_id": None,
                "template_id": "generate_pdf",
                "template_version": "1.0",
                "consent_id": None,
                "webhook_url": "https://workflow.example.org/webhook/generate-pdf",
                "input_payload_sanitized": {"title": "Safe title", "content": "Safe content"},
                "output_summary": "Unsafe response body should never be exposed.",
                "status": "success",
                "error_message": "token secret-value leaked",
                "http_status_code": 200,
                "executed_at": base_time - timedelta(minutes=2),
            },
        )
        workflow_execution_repository.create_execution(
            db,
            {
                "user_id": user_two.id,
                "agent_id": None,
                "skill_id": None,
                "template_id": "other_template",
                "template_version": "2.0",
                "consent_id": None,
                "webhook_url": "https://workflow.example.org/webhook/other",
                "input_payload_sanitized": {"title": "Other title"},
                "output_summary": "Other user response body.",
                "status": "failed",
                "error_message": "Other error",
                "http_status_code": 500,
                "executed_at": base_time - timedelta(minutes=1),
            },
        )
        workflow_execution_repository.create_execution(
            db,
            {
                "user_id": user_one.id,
                "agent_id": None,
                "skill_id": None,
                "template_id": "generate_report",
                "template_version": "1.0",
                "consent_id": None,
                "webhook_url": "https://workflow.example.org/webhook/generate-report",
                "input_payload_sanitized": {"title": "Another safe title"},
                "output_summary": "Another unsafe response body.",
                "status": "failed",
                "error_message": "Webhook returned HTTP 500.",
                "http_status_code": 500,
                "executed_at": base_time,
            },
        )
        db.commit()

    with patch("app.services.auth_service.get_current_active_user", return_value=user_one):
        response = client.get("/workflows/executions/history?limit=10", headers=auth_headers(user_one.id))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2

    first_item = payload["items"][0]
    second_item = payload["items"][1]

    assert first_item["template_id"] == "generate_report"
    assert first_item["template_name"] == "generate_report"
    assert first_item["status"] == "failed"
    assert first_item["agent_id"] is None
    assert first_item["skill_id"] is None
    assert first_item["created_at"]
    assert first_item["completed_at"]
    assert first_item["error_message"] == "Webhook returned HTTP 500."
    assert "output_summary" not in first_item
    assert "input_payload_sanitized" not in first_item
    assert "webhook_url" not in first_item
    assert "consent_id" not in first_item

    assert second_item["template_id"] == "generate_pdf"
    assert second_item["status"] == "success"
    assert second_item["agent_id"] is None
    assert second_item["skill_id"] is None
    assert second_item["error_message"] == "Sensitive error redacted."
    assert "output_summary" not in second_item
    assert "input_payload_sanitized" not in second_item
    assert "webhook_url" not in second_item


def test_workflow_execution_history_empty_returns_safe_empty_list(client):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="workflow-history-empty")
        db.commit()

    with patch("app.services.auth_service.get_current_active_user", return_value=user):
        response = client.get("/workflows/executions/history", headers=auth_headers(user.id))

    assert response.status_code == 200
    payload = response.json()
    assert payload == {"items": []}


def test_workflow_execution_history_limit_is_enforced(client):
    with SessionLocal() as db:
        user = build_user(db, email_prefix="workflow-history-limit")
        base_time = datetime.now(UTC)
        for index in range(3):
            workflow_execution_repository.create_execution(
                db,
                {
                    "user_id": user.id,
                    "agent_id": None,
                    "skill_id": None,
                    "template_id": f"template_{index}",
                    "template_version": "1.0",
                    "consent_id": None,
                    "webhook_url": "https://workflow.example.org/webhook/template",
                    "input_payload_sanitized": {"title": f"Item {index}"},
                    "output_summary": f"Response {index}",
                    "status": "success",
                    "error_message": None,
                    "http_status_code": 200,
                    "executed_at": base_time - timedelta(minutes=index),
                },
            )
        db.commit()

    with patch("app.services.auth_service.get_current_active_user", return_value=user):
        response = client.get("/workflows/executions/history?limit=2", headers=auth_headers(user.id))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2


def test_execute_rejects_disabled_template_without_call(client):
    context = build_execution_context(user_prefix="workflow-exec-disabled")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()
    template["enabled"] = False

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_call:
        response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert response.status_code == 400
    mock_call.assert_not_called()


def test_execute_rejects_private_webhook_url_without_call(client):
    context = build_execution_context(user_prefix="workflow-exec-private")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template(webhook_url="https://127.0.0.1/webhook")

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_call:
        response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"].lower()
    mock_call.assert_not_called()


def test_execute_rejects_version_mismatch_without_call(client):
    context = build_execution_context(user_prefix="workflow-exec-version")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template(version="2.0")

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_call:
        response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert response.status_code == 400
    assert "version mismatch" in response.json()["detail"].lower()
    mock_call.assert_not_called()


def test_execute_rejects_missing_binding_without_call(client):
    context = build_execution_context(user_prefix="workflow-exec-binding", with_binding=False)
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_call:
        response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert response.status_code == 404
    mock_call.assert_not_called()


def test_execute_rejects_non_workflow_skill_without_call(client):
    context = build_execution_context(user_prefix="workflow-exec-prompt")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id, skill_type="prompt_skill")],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_call:
        response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert response.status_code == 400
    assert "workflow_skill" in response.json()["detail"]
    mock_call.assert_not_called()


def test_execute_rejects_inactive_workflow_skill_without_call(client):
    context = build_execution_context(user_prefix="workflow-exec-inactive")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id, is_enabled=False)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_call:
        response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert response.status_code == 400
    assert "active" in response.json()["detail"].lower()
    mock_call.assert_not_called()


def test_execute_rejects_payload_exceeding_template_limit_without_call(client):
    context = build_execution_context(user_prefix="workflow-exec-size")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()
    template["max_payload_bytes"] = 1

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_call:
        response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "A", "content": "B"},
            },
        )

    assert response.status_code == 400
    assert "maximum size" in response.json()["detail"].lower()
    mock_call.assert_not_called()


def test_execute_timeout_and_failed_http_are_audited(client):
    context = build_execution_context(user_prefix="workflow-exec-fail")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()
    timeout_result = WebhookCallResult(
        success=False,
        status_code=None,
        response_summary=None,
        error_message="Webhook request timed out.",
        timed_out=True,
        response_truncated=False,
    )
    failed_result = WebhookCallResult(
        success=False,
        status_code=500,
        response_summary="Internal error summary.",
        error_message="Webhook returned HTTP 500.",
        timed_out=False,
        response_truncated=True,
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook",
        return_value=timeout_result,
    ), patch(
        "app.services.workflow_service.log_service.record_activity",
        return_value=None,
    ):
        timeout_response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert timeout_response.status_code == 200
    assert timeout_response.json()["status"] == "timeout"
    assert timeout_response.json()["http_status_code"] is None

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook",
        return_value=failed_result,
    ), patch(
        "app.services.workflow_service.log_service.record_activity",
        return_value=None,
    ):
        failed_response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert failed_response.status_code == 200
    assert failed_response.json()["status"] == "failed"
    assert failed_response.json()["http_status_code"] == 500

    with SessionLocal() as db:
        executions = workflow_execution_repository.list_executions(db, user_id=context.user.id)
        assert len(executions) == 2
        statuses = {item.status for item in executions}
        assert statuses == {"timeout", "failed"}


def test_execute_rate_limits_after_five_requests(client):
    context = build_execution_context(user_prefix="workflow-exec-ratelimit")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()
    webhook_result = WebhookCallResult(
        success=True,
        status_code=200,
        response_summary="Queued.",
        error_message=None,
        timed_out=False,
        response_truncated=False,
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook",
        return_value=webhook_result,
    ) as mock_call, patch(
        "app.services.workflow_service.log_service.record_activity",
        return_value=None,
    ):
        responses = []
        for _ in range(6):
            responses.append(
                client.post(
                    "/workflows/execute/generate_pdf",
                    headers=headers,
                    json={
                        "agent_id": context.agent_id,
                        "skill_id": context.skill_id,
                        "input_payload": {"title": "Monthly Report", "content": "Content"},
                    },
                )
            )

    assert [response.status_code for response in responses[:5]] == [200, 200, 200, 200, 200]
    assert responses[5].status_code == 429
    assert mock_call.call_count == 5


def test_execute_rejects_missing_agent_or_other_user_agent_without_call(client):
    context = build_execution_context(user_prefix="workflow-exec-agent")
    other_context = build_execution_context(user_prefix="workflow-exec-other")
    current_user = SimpleNamespace(id=context.user.id, role=context.user.role)
    headers = auth_headers(context.user.id)
    template = build_enabled_template()

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[build_workflow_skill_assignment(context.skill_id)],
    ), patch(
        "app.services.workflow_service.call_template_webhook"
    ) as mock_call:
        response = client.post(
            "/workflows/execute/generate_pdf",
            headers=headers,
            json={
                "agent_id": other_context.agent_id,
                "skill_id": context.skill_id,
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert response.status_code == 404
    mock_call.assert_not_called()
