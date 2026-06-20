import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from app.core.security import create_access_token


def auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


def _build_agent(agent_id: uuid.UUID, owner_id: uuid.UUID) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=agent_id,
        owner_id=owner_id,
        name="Agent One",
        slug="agent-one",
        description="Helpful agent",
        role_description="Handles tasks safely.",
        default_model_provider_id=None,
        default_model_name="gpt-4o-mini",
        status="active",
        max_steps=10,
        max_runtime_seconds=300,
        max_token_budget=None,
        requires_approval_by_default=True,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


def test_list_agents_returns_safe_contract(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    agent = _build_agent(uuid.uuid4(), user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_service.list_agents",
        return_value=[agent],
    ):
        response = client.get("/agents", headers=auth_headers(user.id))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["name"] == "Agent One"
    assert "instruction_text" not in payload["items"][0]


def test_create_agent_returns_safe_contract(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    agent = _build_agent(uuid.uuid4(), user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_service.create_agent",
        return_value=agent,
    ):
        response = client.post(
            "/agents",
            headers=auth_headers(user.id),
            json={
                "name": "Agent One",
                "role_description": "Handles tasks safely.",
                "instruction_text": "Follow safe rules.",
                "status": "active",
                "max_steps": 10,
                "max_runtime_seconds": 300,
                "requires_approval_by_default": True,
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["slug"] == "agent-one"
    assert payload["owner_id"] == str(user.id)
    assert "instruction_text" not in payload


def test_get_agent_returns_safe_contract(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    agent_id = uuid.uuid4()
    agent = _build_agent(agent_id, user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_service.get_agent",
        return_value=agent,
    ):
        response = client.get(f"/agents/{agent_id}", headers=auth_headers(user.id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(agent_id)
    assert payload["name"] == "Agent One"
    assert "instruction_text" not in payload
