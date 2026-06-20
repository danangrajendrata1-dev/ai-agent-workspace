import uuid
from types import SimpleNamespace
from unittest.mock import patch

from app.core.security import create_access_token


def auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


def test_register_route_returns_safe_user_shape(client):
    user = SimpleNamespace(
        id=uuid.uuid4(),
        email="new@example.com",
        display_name="New User",
        role="user",
        subscription_plan="free",
        is_active=True,
    )

    with patch("app.services.auth_service.register_user", return_value=user):
        response = client.post(
            "/auth/register",
            json={
                "email": "new@example.com",
                "password": "password123",
                "display_name": "New User",
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == "new@example.com"
    assert payload["role"] == "user"
    assert payload["subscription_plan"] == "free"
    assert "password" not in payload
    assert "access_token" not in payload


def test_login_route_returns_bearer_token_only(client):
    with patch("app.services.auth_service.authenticate_user", return_value="token-123"):
        response = client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "password123",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload == {"access_token": "token-123", "token_type": "bearer"}


def test_me_route_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_route_returns_current_user_shape(client):
    user = SimpleNamespace(
        id=uuid.uuid4(),
        email="owner@example.com",
        display_name="Owner User",
        role="admin",
        subscription_plan="pro",
        is_active=True,
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=user):
        response = client.get("/auth/me", headers=auth_headers(user.id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "owner@example.com"
    assert payload["display_name"] == "Owner User"
    assert payload["role"] == "admin"
    assert payload["subscription_plan"] == "pro"
    assert payload["is_active"] is True
    assert "password" not in payload
