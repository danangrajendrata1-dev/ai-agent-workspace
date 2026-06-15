import unittest
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.schemas.model_provider_api_key import ModelProviderApiKeySaveRequest
from app.services.model_provider_api_key_service import (
    delete_provider_api_key,
    get_provider_api_key_status,
    list_provider_api_key_statuses,
    save_provider_api_key,
)


def build_record(
    owner_id: uuid.UUID,
    *,
    provider: str = "openai",
    encrypted_api_key: str = "encrypted-value",
    key_last4: str = "abcd",
    key_prefix_masked: str = "********",
    connection_status: str = "connected",
):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        provider=provider,
        encrypted_api_key=encrypted_api_key,
        key_last4=key_last4,
        key_prefix_masked=key_prefix_masked,
        connection_status=connection_status,
        created_at=now,
        updated_at=now,
    )


class ModelProviderApiKeyVaultTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.owner_id = uuid.uuid4()

    def test_save_encrypts_api_key_and_masks_response(self):
        payload = ModelProviderApiKeySaveRequest.model_validate({"api_key": "sk-live-12345678"})
        created_record = build_record(self.owner_id, provider="openai", key_last4="5678")

        with patch(
            "app.services.model_provider_api_key_service.model_provider_api_key_repository.get_by_owner_and_provider",
            return_value=None,
        ), patch(
            "app.services.model_provider_api_key_service.model_provider_api_key_repository.create",
            return_value=created_record,
        ) as mock_create, patch(
            "app.services.model_provider_api_key_service.log_service.record_activity"
        ) as mock_log:
            result = save_provider_api_key(
                self.db,
                owner_id=self.owner_id,
                provider="openai",
                payload=payload,
            )

        created_kwargs = mock_create.call_args.kwargs
        self.assertNotEqual(created_kwargs["encrypted_api_key"], "sk-live-12345678")
        self.assertEqual(created_kwargs["key_last4"], "5678")
        self.assertNotIn("sk-live-12345678", str(created_kwargs))
        self.assertEqual(result.provider, "openai")
        self.assertEqual(result.connection_status, "connected")
        self.assertEqual(result.masked_key, "********5678")
        self.assertEqual(result.key_last4, "5678")
        self.assertNotIn("api_key", result.model_dump())
        self.assertNotIn("sk-live-12345678", str(mock_log.call_args.kwargs))

    def test_get_and_list_do_not_return_raw_api_key(self):
        record = build_record(self.owner_id, provider="anthropic", key_last4="bc12")

        with patch(
            "app.services.model_provider_api_key_service.model_provider_api_key_repository.get_by_owner_and_provider",
            return_value=record,
        ):
            single = get_provider_api_key_status(self.db, owner_id=self.owner_id, provider="anthropic")

        with patch(
            "app.services.model_provider_api_key_service.model_provider_api_key_repository.list_by_owner",
            return_value=[record],
        ):
            listing = list_provider_api_key_statuses(self.db, owner_id=self.owner_id)

        self.assertNotIn("api_key", single.model_dump())
        self.assertNotIn("encrypted_api_key", single.model_dump())
        self.assertEqual(single.masked_key, "********bc12")
        self.assertNotIn("api_key", listing.model_dump())
        self.assertEqual(listing.items[0].provider, "openai")

    def test_owner_isolation_uses_current_user_only(self):
        other_owner_id = uuid.uuid4()
        record = build_record(other_owner_id, provider="openai")

        with patch(
            "app.services.model_provider_api_key_service.model_provider_api_key_repository.get_by_owner_and_provider",
            return_value=record,
        ) as mock_get:
            status = get_provider_api_key_status(self.db, owner_id=self.owner_id, provider="openai")

        mock_get.assert_called_once_with(self.db, self.owner_id, "openai")
        self.assertEqual(status.owner_id, other_owner_id)

    def test_invalid_provider_is_rejected(self):
        payload = ModelProviderApiKeySaveRequest.model_validate({"api_key": "sk-live-12345678"})

        with self.assertRaises(HTTPException) as exc_info:
            save_provider_api_key(self.db, owner_id=self.owner_id, provider="bogus", payload=payload)

        self.assertEqual(exc_info.exception.status_code, 400)

    def test_ollama_local_is_rejected_for_api_key_storage(self):
        payload = ModelProviderApiKeySaveRequest.model_validate({"api_key": "sk-live-12345678"})

        with self.assertRaises(HTTPException) as exc_info:
            save_provider_api_key(self.db, owner_id=self.owner_id, provider="ollama_local", payload=payload)

        self.assertEqual(exc_info.exception.status_code, 400)

    def test_delete_removes_key_and_returns_disconnected_status(self):
        record = build_record(self.owner_id, provider="openrouter", key_last4="ef12")

        with patch(
            "app.services.model_provider_api_key_service.model_provider_api_key_repository.get_by_owner_and_provider",
            return_value=record,
        ), patch(
            "app.services.model_provider_api_key_service.model_provider_api_key_repository.delete"
        ) as mock_delete, patch(
            "app.services.model_provider_api_key_service.log_service.record_activity"
        ) as mock_log:
            result = delete_provider_api_key(self.db, owner_id=self.owner_id, provider="openrouter")

        mock_delete.assert_called_once_with(self.db, record)
        self.assertEqual(result.connection_status, "not_connected")
        self.assertIsNone(result.masked_key)
        self.assertNotIn("sk-live-12345678", str(mock_log.call_args.kwargs))

    def test_missing_encryption_key_fails_safely(self):
        payload = ModelProviderApiKeySaveRequest.model_validate({"api_key": "sk-live-12345678"})

        with patch(
            "app.services.model_provider_api_key_service.model_provider_api_key_repository.get_by_owner_and_provider",
            return_value=None,
        ), patch(
            "app.core.provider_api_keys.get_settings",
            return_value=SimpleNamespace(provider_api_key_encryption_key=None),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                save_provider_api_key(self.db, owner_id=self.owner_id, provider="openai", payload=payload)

        self.assertEqual(exc_info.exception.status_code, 500)
        self.assertIn("encryption is not configured", exc_info.exception.detail)

    def test_missing_key_status_is_not_connected(self):
        with patch(
            "app.services.model_provider_api_key_service.model_provider_api_key_repository.get_by_owner_and_provider",
            return_value=None,
        ):
            result = get_provider_api_key_status(self.db, owner_id=self.owner_id, provider="custom")

        self.assertEqual(result.connection_status, "not_connected")
        self.assertIsNone(result.masked_key)


if __name__ == "__main__":
    unittest.main()
