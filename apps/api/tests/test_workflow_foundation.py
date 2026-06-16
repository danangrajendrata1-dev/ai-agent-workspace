import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.database import SessionLocal
from app.repositories import (
    skill_repository,
    workflow_consent_repository,
    workflow_execution_repository,
    workflow_skill_binding_repository,
)
from app.services.workflow_service import clear_workflow_rate_limiter

from .test_sessions import auth_headers, build_user


@pytest.fixture(autouse=True)
def reset_workflow_rate_limiter():
    clear_workflow_rate_limiter()


def build_skill(db, *, name: str, source_type: str = "manual"):
    skill = skill_repository.create(
        db,
        {
            "name": name,
            "slug": f"{name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}",
            "description": f"{name} description.",
            "content": f"{name} content.",
            "source_type": source_type,
            "source_id": None,
            "version_label": "1.0",
            "risk_level": "medium",
            "status": "active",
        },
    )
    db.commit()
    db.refresh(skill)
    return skill


def test_workflow_consent_create_is_idempotent_and_owner_specific(client):
    user_one_template = {
        "id": "generate_pdf",
        "name": "Generate PDF",
        "description": "Membuat file PDF dari teks",
        "webhook_url": "https://workflow.example.com/webhook/generate-pdf",
        "input_schema": {"title": "string", "content": "string"},
        "output_type": "json",
        "enabled": True,
        "template_version": "1.0",
        "risk_level": "medium",
        "max_payload_bytes": 10000,
    }

    with SessionLocal() as db:
        user_one = build_user(db, email_prefix="workflow-consent-one")
        user_two = build_user(db, email_prefix="workflow-consent-two")

    with patch("app.services.auth_service.get_current_active_user", return_value=user_one), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=user_one_template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.log_service.record_activity",
        return_value=None,
    ):
        response_one = client.post("/workflows/consent/generate_pdf", headers=auth_headers(user_one.id))

    assert response_one.status_code == 201
    consent_one = response_one.json()

    with patch("app.services.auth_service.get_current_active_user", return_value=user_one), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=user_one_template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.log_service.record_activity",
        return_value=None,
    ):
        response_two = client.post("/workflows/consent/generate_pdf", headers=auth_headers(user_one.id))

    assert response_two.status_code == 201
    assert response_two.json()["id"] == consent_one["id"]

    with patch("app.services.auth_service.get_current_active_user", return_value=user_two):
        response_list = client.get("/workflows/consents", headers=auth_headers(user_two.id))

    assert response_list.status_code == 200
    assert response_list.json()["items"] == []

    with SessionLocal() as db:
        consents = workflow_consent_repository.list_consents(db, user_id=user_one.id)
        assert len(consents) == 1
        assert consents[0].template_version == "1.0"
        assert consents[0].template_id == "generate_pdf"


def test_workflow_binding_create_list_delete_are_owner_only(client):
    template = {
        "id": "generate_pdf",
        "name": "Generate PDF",
        "description": "Membuat file PDF dari teks",
        "webhook_url": "https://workflow.example.com/webhook/generate-pdf",
        "input_schema": {"title": "string", "content": "string"},
        "output_type": "json",
        "enabled": True,
        "template_version": "1.0",
        "risk_level": "medium",
        "max_payload_bytes": 10000,
    }

    with SessionLocal() as db:
        user_one = build_user(db, email_prefix="workflow-bind-one")
        user_two = build_user(db, email_prefix="workflow-bind-two")
        skill_one = build_skill(db, name="Workflow Skill One")
        skill_two = build_skill(db, name="Workflow Skill Two")
        skill_one_id = skill_one.id
        skill_two_id = skill_two.id

    routed_agent = SimpleNamespace(id=uuid.uuid4())
    assignment = SimpleNamespace(
        skill_id=skill_one_id,
        skill=SimpleNamespace(title="Workflow Skill One", type="workflow_skill", status="active"),
        is_enabled=True,
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=user_one), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.agent_repository.list_by_owner",
        return_value=[routed_agent],
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[assignment],
    ), patch(
        "app.services.workflow_service.log_service.record_activity",
        return_value=None,
    ):
        response = client.post(
            "/workflows/bindings",
            headers=auth_headers(user_one.id),
            json={"skill_id": str(skill_one_id), "template_id": "generate_pdf"},
        )

    assert response.status_code == 201
    binding = response.json()
    assert binding["skill_name"] == "Workflow Skill One"
    assert binding["skill_type"] == "workflow_skill"

    with SessionLocal() as db:
        workflow_skill_binding_repository.create_binding(
            db,
            user_id=user_two.id,
            skill_id=skill_two_id,
            template_id="generate_pdf",
            template_version="1.0",
        )
        db.commit()

    with patch("app.services.auth_service.get_current_active_user", return_value=user_one):
        response_list = client.get("/workflows/bindings", headers=auth_headers(user_one.id))

    assert response_list.status_code == 200
    assert len(response_list.json()["items"]) == 1
    assert response_list.json()["items"][0]["skill_name"] == "Workflow Skill One"

    with patch("app.services.auth_service.get_current_active_user", return_value=user_two):
        response_other = client.get("/workflows/bindings", headers=auth_headers(user_two.id))

    assert response_other.status_code == 200
    assert len(response_other.json()["items"]) == 1
    other_binding_id = response_other.json()["items"][0]["id"]

    with patch("app.services.auth_service.get_current_active_user", return_value=user_one):
        response_delete_other = client.delete(
            f"/workflows/bindings/{other_binding_id}",
            headers=auth_headers(user_one.id),
        )

    assert response_delete_other.status_code == 404

    with patch("app.services.auth_service.get_current_active_user", return_value=user_one), patch(
        "app.services.workflow_service.log_service.record_activity",
        return_value=None,
    ):
        response_delete_own = client.delete(
            f"/workflows/bindings/{binding['id']}",
            headers=auth_headers(user_one.id),
        )

    assert response_delete_own.status_code == 204

    with SessionLocal() as db:
        assert workflow_skill_binding_repository.get_binding_by_id(
            db,
            user_id=user_one.id,
            binding_id=uuid.UUID(binding["id"]),
        ) is None


def test_workflow_binding_rejects_non_workflow_skill(client):
    template = {
        "id": "generate_pdf",
        "name": "Generate PDF",
        "description": "Membuat file PDF dari teks",
        "webhook_url": "https://workflow.example.com/webhook/generate-pdf",
        "input_schema": {"title": "string", "content": "string"},
        "output_type": "json",
        "enabled": True,
        "template_version": "1.0",
        "risk_level": "medium",
        "max_payload_bytes": 10000,
    }

    with SessionLocal() as db:
        user = build_user(db, email_prefix="workflow-bind-reject")
        skill = build_skill(db, name="Knowledge Skill")
        skill_id = skill.id

    assignment = SimpleNamespace(
        skill_id=skill_id,
        skill=SimpleNamespace(title="Knowledge Skill", type="knowledge_skill", status="active"),
        is_enabled=True,
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.agent_repository.list_by_owner",
        return_value=[SimpleNamespace(id=uuid.uuid4())],
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[assignment],
    ):
        response = client.post(
            "/workflows/bindings",
            headers=auth_headers(user.id),
            json={"skill_id": str(skill_id), "template_id": "generate_pdf"},
        )

    assert response.status_code == 400
    assert "workflow_skill" in response.json()["detail"]


def test_workflow_binding_rejects_skill_not_owned_by_user(client):
    template = {
        "id": "generate_pdf",
        "name": "Generate PDF",
        "description": "Membuat file PDF dari teks",
        "webhook_url": "https://workflow.example.com/webhook/generate-pdf",
        "input_schema": {"title": "string", "content": "string"},
        "output_type": "json",
        "enabled": True,
        "template_version": "1.0",
        "risk_level": "medium",
        "max_payload_bytes": 10000,
    }

    with SessionLocal() as db:
        user = build_user(db, email_prefix="workflow-bind-owner")
        other_skill = build_skill(db, name="Other Skill")
        other_skill_id = other_skill.id

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.agent_repository.list_by_owner",
        return_value=[],
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[],
    ):
        response = client.post(
            "/workflows/bindings",
            headers=auth_headers(user.id),
            json={"skill_id": str(other_skill_id), "template_id": "generate_pdf"},
        )

    assert response.status_code == 404


def test_workflow_binding_rejects_disabled_template(client):
    template = {
        "id": "generate_pdf",
        "name": "Generate PDF",
        "description": "Membuat file PDF dari teks",
        "webhook_url": "https://workflow.example.com/webhook/generate-pdf",
        "input_schema": {"title": "string", "content": "string"},
        "output_type": "json",
        "enabled": False,
        "template_version": "1.0",
        "risk_level": "medium",
        "max_payload_bytes": 10000,
    }

    with SessionLocal() as db:
        user = build_user(db, email_prefix="workflow-bind-disabled")
        skill = build_skill(db, name="Workflow Skill Disabled")
        skill_id = skill.id

    assignment = SimpleNamespace(
        skill_id=skill_id,
        skill=SimpleNamespace(title="Workflow Skill Disabled", type="workflow_skill", status="active"),
        is_enabled=True,
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.workflow_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_service.validate_safe_webhook_url",
        return_value=(True, None),
    ), patch(
        "app.services.workflow_service.agent_repository.list_by_owner",
        return_value=[SimpleNamespace(id=uuid.uuid4())],
    ), patch(
        "app.services.workflow_service.skill_service.list_active_agent_skills",
        return_value=[assignment],
    ):
        response = client.post(
            "/workflows/bindings",
            headers=auth_headers(user.id),
            json={"skill_id": str(skill_id), "template_id": "generate_pdf"},
        )

    assert response.status_code == 400
    assert "disabled" in response.json()["detail"].lower()


def test_workflow_execution_history_is_owner_only_and_summary_only(client):
    with SessionLocal() as db:
        user_one = build_user(db, email_prefix="workflow-execution-one")
        user_two = build_user(db, email_prefix="workflow-execution-two")
        workflow_execution_repository.create_execution(
            db,
            {
                "user_id": user_one.id,
                "agent_id": None,
                "skill_id": None,
                "template_id": "generate_pdf",
                "template_version": "1.0",
                "consent_id": None,
                "webhook_url": "https://workflow.example.com/webhook/generate-pdf",
                "input_payload_sanitized": {"title": "Safe title"},
                "output_summary": "Safe execution summary.",
                "status": "completed",
                "error_message": None,
                "http_status_code": 200,
            },
        )
        workflow_execution_repository.create_execution(
            db,
            {
                "user_id": user_two.id,
                "agent_id": None,
                "skill_id": None,
                "template_id": "generate_pdf",
                "template_version": "1.0",
                "consent_id": None,
                "webhook_url": "https://workflow.example.com/webhook/generate-pdf",
                "input_payload_sanitized": {"title": "Other title"},
                "output_summary": "Other execution summary.",
                "status": "completed",
                "error_message": None,
                "http_status_code": 200,
            },
        )
        db.commit()

    with patch("app.services.auth_service.get_current_active_user", return_value=user_one):
        response = client.get("/workflows/executions", headers=auth_headers(user_one.id))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    execution = payload["items"][0]
    assert execution["template_id"] == "generate_pdf"
    assert execution["output_summary"] == "Safe execution summary."
    assert "webhook_url" not in execution
    assert "input_payload_sanitized" not in execution
