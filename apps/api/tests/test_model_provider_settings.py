import unittest
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from app.schemas.model_provider_setting import ModelProviderSettingsResponse, ModelProviderSettingsUpdate
from app.services.model_provider_settings_service import get_settings, update_settings


def build_setting(
    owner_id: uuid.UUID,
    *,
    preferred_provider: str | None = None,
    preferred_model: str | None = None,
    connection_status: str = "not_connected",
):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        preferred_provider=preferred_provider,
        preferred_model=preferred_model,
        connection_status=connection_status,
        created_at=now,
        updated_at=now,
    )


class ModelProviderSettingsTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.owner_id = uuid.uuid4()

    def test_default_settings_are_safe(self):
        created_setting = build_setting(self.owner_id)

        with patch(
            "app.services.model_provider_settings_service.model_provider_setting_repository.get_by_owner_id",
            return_value=None,
        ), patch(
            "app.services.model_provider_settings_service.model_provider_setting_repository.create_default",
            return_value=created_setting,
        ) as mock_create_default:
            result = get_settings(self.db, owner_id=self.owner_id)

        self.assertEqual(result.preferred_provider, None)
        self.assertEqual(result.preferred_model, None)
        self.assertEqual(result.connection_status, "not_connected")
        mock_create_default.assert_called_once_with(self.db, self.owner_id)

    def test_allowed_provider_can_be_saved(self):
        existing_setting = build_setting(self.owner_id)
        saved_setting = build_setting(
            self.owner_id,
            preferred_provider="openai",
            preferred_model="gpt-4o-mini",
            connection_status="metadata_configured",
        )
        payload = ModelProviderSettingsUpdate.model_validate(
            {"preferred_provider": "openai", "preferred_model": "gpt-4o-mini"}
        )

        with patch(
            "app.services.model_provider_settings_service.model_provider_setting_repository.get_by_owner_id",
            return_value=existing_setting,
        ), patch(
            "app.services.model_provider_settings_service.model_provider_setting_repository.update",
            return_value=saved_setting,
        ) as mock_update, patch(
            "app.services.model_provider_settings_service.log_service.record_activity"
        ) as mock_activity, patch(
            "app.services.model_provider_settings_service.log_service.record_audit"
        ) as mock_audit:
            result = update_settings(self.db, owner_id=self.owner_id, payload=payload)

        self.assertEqual(result.preferred_provider, "openai")
        self.assertEqual(result.preferred_model, "gpt-4o-mini")
        self.assertEqual(result.connection_status, "metadata_configured")
        update_data = mock_update.call_args.args[2]
        self.assertEqual(update_data["preferred_provider"], "openai")
        self.assertEqual(update_data["preferred_model"], "gpt-4o-mini")
        self.assertEqual(update_data["connection_status"], "metadata_configured")
        self.assertEqual(mock_activity.call_args.kwargs["event_type"], "model_provider_settings.updated")
        self.assertEqual(mock_activity.call_args.kwargs["actor_id"], self.owner_id)
        self.assertEqual(mock_audit.call_args.kwargs["action"], "update")
        self.assertEqual(mock_audit.call_args.kwargs["entity_type"], "model_provider_settings")
        self.assertNotIn("api_key", str(mock_activity.call_args.kwargs))

    def test_invalid_provider_is_rejected(self):
        with self.assertRaises(ValidationError):
            ModelProviderSettingsUpdate.model_validate({"preferred_provider": "bogus"})

    def test_preferred_model_cannot_contain_secret_like_content(self):
        with self.assertRaises(ValidationError):
            ModelProviderSettingsUpdate.model_validate(
                {"preferred_provider": "openai", "preferred_model": "sk-live-example-token"}
            )

    def test_update_payload_forbids_raw_secret_fields(self):
        with self.assertRaises(ValidationError):
            ModelProviderSettingsUpdate.model_validate(
                {
                    "preferred_provider": "openai",
                    "preferred_model": "gpt-4o-mini",
                    "api_key": "secret-value",
                }
            )

    def test_response_schema_exposes_only_safe_fields(self):
        self.assertNotIn("api_key", ModelProviderSettingsResponse.model_fields)
        self.assertNotIn("oauth_token", ModelProviderSettingsResponse.model_fields)
        self.assertNotIn("refresh_token", ModelProviderSettingsResponse.model_fields)


if __name__ == "__main__":
    unittest.main()
