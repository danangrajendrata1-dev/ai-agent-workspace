import uuid
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.core.subscription_plans import DEFAULT_REGISTER_ROLE, DEFAULT_REGISTER_SUBSCRIPTION_PLAN
from app.schemas.auth import CurrentUserResponse, RegisterRequest
from app.services.auth_service import bootstrap_owner, register_user


class AuthRegistrationTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

    def test_register_user_defaults_to_user_and_free_plan(self):
        created_user = SimpleNamespace(
            id="user-id",
            email="new@example.com",
            display_name="New User",
            role=DEFAULT_REGISTER_ROLE,
            subscription_plan=DEFAULT_REGISTER_SUBSCRIPTION_PLAN,
            is_active=True,
        )

        with patch("app.services.auth_service.user_repository.get_by_email", return_value=None), patch(
            "app.services.auth_service.user_repository.create_user",
            return_value=created_user,
        ) as mock_create_user, patch("app.services.auth_service.hash_password", return_value="hashed-password"), patch(
            "app.services.auth_service.log_service.record_activity"
        ) as mock_record_activity:
            result = register_user(self.db, email=" New@Example.com ", password="password123", display_name=" New User ")

        self.assertEqual(result, created_user)
        mock_create_user.assert_called_once_with(
            self.db,
            email="new@example.com",
            password_hash="hashed-password",
            display_name="New User",
            role=DEFAULT_REGISTER_ROLE,
            subscription_plan=DEFAULT_REGISTER_SUBSCRIPTION_PLAN,
        )
        mock_record_activity.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(created_user)

    def test_register_user_rejects_duplicate_email(self):
        with patch(
            "app.services.auth_service.user_repository.get_by_email",
            return_value=SimpleNamespace(id="existing"),
        ), patch("app.services.auth_service.user_repository.create_user") as mock_create_user:
            with self.assertRaises(HTTPException) as exc_info:
                register_user(self.db, email="existing@example.com", password="password123", display_name="Existing")

        self.assertEqual(exc_info.exception.status_code, 400)
        mock_create_user.assert_not_called()
        self.db.commit.assert_not_called()

    def test_bootstrap_owner_creates_admin_user(self):
        created_user = SimpleNamespace(
            id="admin-id",
            email="admin@example.com",
            display_name="Admin User",
            role="admin",
            subscription_plan=DEFAULT_REGISTER_SUBSCRIPTION_PLAN,
            is_active=True,
        )

        with patch("app.services.auth_service.user_repository.count_active_users", return_value=0), patch(
            "app.services.auth_service.user_repository.get_by_email",
            return_value=None,
        ), patch(
            "app.services.auth_service.user_repository.create_admin_user",
            return_value=created_user,
        ) as mock_create_admin_user, patch("app.services.auth_service.hash_password", return_value="hashed-password"), patch(
            "app.services.auth_service.log_service.record_activity"
        ) as mock_record_activity:
            result = bootstrap_owner(
                self.db,
                email=" Admin@Example.com ",
                password="password123",
                display_name=" Admin User ",
            )

        self.assertEqual(result, created_user)
        mock_create_admin_user.assert_called_once_with(
            self.db,
            email="admin@example.com",
            password_hash="hashed-password",
            display_name="Admin User",
        )
        mock_record_activity.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(created_user)

    def test_register_request_forbids_role_and_plan_fields(self):
        with self.assertRaises(ValidationError):
            RegisterRequest.model_validate(
                {
                    "email": "new@example.com",
                    "password": "password123",
                    "display_name": "New User",
                    "role": "admin",
                    "subscription_plan": "pro",
                }
            )

    def test_current_user_response_normalizes_legacy_owner_role(self):
        user = SimpleNamespace(
            id=uuid.uuid4(),
            email="owner@example.com",
            display_name="Owner User",
            role="owner",
            subscription_plan="free",
            is_active=True,
        )

        result = CurrentUserResponse.model_validate(user)

        self.assertEqual(result.role, "admin")
        self.assertEqual(result.subscription_plan, "free")


if __name__ == "__main__":
    unittest.main()
