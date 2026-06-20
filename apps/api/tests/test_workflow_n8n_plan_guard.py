from types import SimpleNamespace
from unittest.mock import patch

from .test_sessions import auth_headers


def make_user(*, plan: str = "free"):
    return SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        role="user",
        subscription_plan=plan,
        is_active=True,
        deleted_at=None,
    )


def test_workflow_templates_block_free_plan(client):
    user = make_user(plan="free")

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.workflow_service.get_workflow_templates"
    ) as mock_get_templates:
        response = client.get("/workflows/templates", headers=auth_headers(user.id))

    assert response.status_code == 403
    assert "n8n access" in response.text
    mock_get_templates.assert_not_called()


def test_workflow_consent_block_free_plan(client):
    user = make_user(plan="free")

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.workflow_service.get_workflow_template"
    ) as mock_get_template:
        response = client.post("/workflows/consent/generate_pdf", headers=auth_headers(user.id))

    assert response.status_code == 403
    assert "n8n access" in response.text
    mock_get_template.assert_not_called()


def test_workflow_execute_block_free_plan_before_webhook(client):
    user = make_user(plan="free")

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.workflow_service.get_workflow_template"
    ) as mock_get_template, patch("app.services.workflow_service.call_template_webhook") as mock_call:
        response = client.post(
            "/workflows/execute/generate_pdf",
            headers=auth_headers(user.id),
            json={
                "agent_id": "22222222-2222-2222-2222-222222222222",
                "skill_id": "33333333-3333-3333-3333-333333333333",
                "input_payload": {"title": "Monthly Report", "content": "Content"},
            },
        )

    assert response.status_code == 403
    assert "n8n access" in response.text
    mock_get_template.assert_not_called()
    mock_call.assert_not_called()
