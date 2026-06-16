import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.security import create_access_token
from app.services.provider_test_service import clear_provider_test_rate_limiter


def auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


@pytest.fixture(autouse=True)
def reset_provider_test_rate_limiter():
    clear_provider_test_rate_limiter()
    yield
    clear_provider_test_rate_limiter()


def test_requires_authentication(client):
    response = client.post("/providers/test-connection", json={"provider": "openai"})

    assert response.status_code == 401


def test_invalid_provider_is_rejected(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user):
        response = client.post("/providers/test-connection", headers=headers, json={"provider": "bogus"})

    assert response.status_code == 422


def test_missing_api_key_returns_safe_message(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.provider_test_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=None,
    ):
        response = client.post("/providers/test-connection", headers=headers, json={"provider": "openai"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["provider"] == "openai"
    assert payload["message"] == "No API key found for this provider"


def test_placeholder_provider_returns_safe_message(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    record = SimpleNamespace(encrypted_api_key="ignored")

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.provider_test_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=record,
    ), patch(
        "app.services.provider_test_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ):
        response = client.post(
            "/providers/test-connection",
            headers=headers,
            json={"provider": "custom"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["message"] == "Provider not yet integrated"


def test_success_response_is_safe(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    record = SimpleNamespace(encrypted_api_key="encrypted")

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.provider_test_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=record,
    ), patch(
        "app.services.provider_test_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.provider_test_service.build_provider_connection_probe",
        return_value=lambda api_key: SimpleNamespace(success=True),
    ):
        response = client.post("/providers/test-connection", headers=headers, json={"provider": "openai"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Connection successful"
    assert "encrypted" not in response.text
    assert "Say: connection ok" not in response.text


def test_unauthorized_response_is_safe(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    record = SimpleNamespace(encrypted_api_key="encrypted")

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.provider_test_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=record,
    ), patch(
        "app.services.provider_test_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.provider_test_service.build_provider_connection_probe",
        return_value=lambda api_key: (_ for _ in ()).throw(Exception("raw secret should not leak")),
    ):
        response = client.post("/providers/test-connection", headers=headers, json={"provider": "openai"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["message"] == "Invalid API key or unauthorized"
    assert "raw secret should not leak" not in response.text
    assert "encrypted" not in response.text


def test_rate_limit_blocks_sixth_request(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    record = SimpleNamespace(encrypted_api_key="encrypted")

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.provider_test_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=record,
    ), patch(
        "app.services.provider_test_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.provider_test_service.build_provider_connection_probe",
        return_value=lambda api_key: SimpleNamespace(success=True),
    ):
        statuses = []
        for _ in range(6):
            response = client.post(
                "/providers/test-connection",
                headers=headers,
                json={"provider": "openai"},
            )
            statuses.append(response.status_code)

    assert statuses[:5] == [200, 200, 200, 200, 200]
    assert statuses[5] == 429


def test_no_real_provider_call_when_mocked(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    record = SimpleNamespace(encrypted_api_key="encrypted")

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.provider_test_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=record,
    ), patch(
        "app.services.provider_test_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.provider_test_service._post_json",
        side_effect=AssertionError("real provider call must not happen in test"),
    ), patch(
        "app.services.provider_test_service.build_provider_connection_probe",
        return_value=lambda api_key: SimpleNamespace(success=True),
    ):
        response = client.post("/providers/test-connection", headers=headers, json={"provider": "openai"})

    assert response.status_code == 200
