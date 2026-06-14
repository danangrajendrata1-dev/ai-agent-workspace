import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import uuid

from app.services.github_import_service import (
    approve_github_skill_import,
    disable_github_import,
    preview_github_skill,
    reject_github_import,
)


class GitHubImportLoggingTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.import_id = uuid.uuid4()
        self.github_import = SimpleNamespace(
            id=self.import_id,
            repo_url="https://github.com/example/repo",
            branch="main",
            commit_sha=None,
            import_type="skill",
            file_path="SKILL.md",
            content_preview='{"name":"Email Summary","version":"1.0.0","description":"Generate summary."}',
            status="preview",
            review_notes=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.preview_payload = SimpleNamespace(
            repo_url="https://github.com/example/repo",
            branch="main",
            file_path="SKILL.md",
        )
        self.approve_payload = SimpleNamespace(
            name="Email Summary",
            slug=None,
            description="Generate summary.",
            version_label="1.0.0",
            risk_level="medium",
            status="active",
            review_notes="reviewed",
        )

    def test_preview_logs_metadata_only(self):
        with patch("app.services.github_import_service.fetch_text_preview", return_value=("raw-url", "raw content")), patch(
            "app.services.github_import_service.github_import_repository.create_preview",
            return_value=self.github_import,
        ), patch("app.services.github_import_service.log_service.record_activity") as mock_record_activity:
            preview_github_skill(self.db, self.preview_payload)

        mock_record_activity.assert_called_once()
        metadata = mock_record_activity.call_args.kwargs["metadata_json"]
        self.assertEqual(metadata["import_id"], str(self.import_id))
        self.assertEqual(metadata["repo_url"], self.github_import.repo_url)
        self.assertEqual(metadata["file_path"], self.github_import.file_path)
        self.assertNotIn("raw content", str(metadata))

    def test_unsafe_manifest_logs_blocked_import_without_preview_content(self):
        with patch("app.services.github_import_service.github_import_repository.get_by_id", return_value=self.github_import), patch(
            "app.services.github_import_service.inspect_skill_manifest_content",
            return_value=SimpleNamespace(
                is_safe=False,
                errors=["validation: name is required"],
                warnings=[],
                normalized_manifest=None,
                is_extracted=True,
                is_valid=False,
                source_format="json",
            ),
        ), patch("app.services.github_import_service.log_service.record_activity") as mock_record_activity, patch(
            "app.services.github_import_service.log_service.record_audit"
        ) as mock_record_audit:
            with self.assertRaises(Exception):
                approve_github_skill_import(self.db, self.import_id, self.approve_payload)

        self.assertGreaterEqual(mock_record_activity.call_count, 1)
        self.assertGreaterEqual(mock_record_audit.call_count, 1)
        for call in mock_record_activity.call_args_list:
            self.assertNotIn(self.github_import.content_preview, str(call))

    def test_successful_import_logs_import_and_audit(self):
        inspection = SimpleNamespace(
            is_safe=True,
            errors=[],
            warnings=[],
            normalized_manifest={
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate summary.",
                "author": None,
                "required_capabilities": [],
                "required_tools": [],
                "required_credentials": [],
                "required_domains": [],
                "n8n_workflow": None,
                "permissions_requested": [],
                "safety_notes": None,
            },
            is_extracted=True,
            is_valid=True,
            source_format="json",
        )

        with patch("app.services.github_import_service.github_import_repository.get_by_id", return_value=self.github_import), patch(
            "app.services.github_import_service.inspect_skill_manifest_content",
            return_value=inspection,
        ), patch("app.services.github_import_service.assess_skill_manifest_risk") as mock_assess, patch(
            "app.services.github_import_service.ensure_unique_skill_slug",
            return_value="email-summary",
        ), patch("app.services.github_import_service.skill_repository.create", return_value=SimpleNamespace(id=uuid.uuid4(), status="inactive")) as mock_create, patch(
            "app.services.github_import_service.github_import_repository.update_status"
        ) as mock_update_status, patch(
            "app.services.github_import_service.github_import_repository.update_review_notes"
        ) as mock_update_review_notes, patch(
            "app.services.github_import_service.serialize_github_import",
            return_value=SimpleNamespace(status="imported"),
        ), patch("app.services.github_import_service.log_service.record_activity") as mock_record_activity, patch(
            "app.services.github_import_service.log_service.record_audit"
        ) as mock_record_audit:
            mock_assess.return_value = SimpleNamespace(
                risk_level="low",
                reasons=["Metadata-only manifest."],
                requires_review=False,
                is_blocked=False,
            )
            approve_github_skill_import(self.db, self.import_id, self.approve_payload)

        mock_create.assert_called_once()
        self.assertGreaterEqual(mock_record_activity.call_count, 1)
        self.assertGreaterEqual(mock_record_audit.call_count, 1)
        self.assertEqual(mock_update_status.call_args.args[2], "imported")
        self.assertEqual(mock_update_review_notes.call_args.args[2], "reviewed")

    def test_reject_logs_metadata(self):
        with patch("app.services.github_import_service.github_import_repository.get_by_id", return_value=self.github_import), patch(
            "app.services.github_import_service.github_import_repository.update_status"
        ), patch(
            "app.services.github_import_service.github_import_repository.update_review_notes"
        ), patch("app.services.github_import_service.log_service.record_activity") as mock_record_activity, patch(
            "app.services.github_import_service.log_service.record_audit"
        ) as mock_record_audit:
            reject_github_import(self.db, self.import_id, SimpleNamespace(review_notes="nope"))

        self.assertEqual(mock_record_activity.call_args.kwargs["event_type"], "github_import_rejected")
        self.assertEqual(mock_record_audit.call_args.kwargs["action"], "github_import_rejected")

    def test_disable_logs_metadata(self):
        with patch("app.services.github_import_service.github_import_repository.get_by_id", return_value=self.github_import), patch(
            "app.services.github_import_service.github_import_repository.update_status"
        ), patch("app.services.github_import_service.log_service.record_activity") as mock_record_activity, patch(
            "app.services.github_import_service.log_service.record_audit"
        ) as mock_record_audit:
            disable_github_import(self.db, self.import_id)

        self.assertEqual(mock_record_activity.call_args.kwargs["event_type"], "github_import_disabled")
        self.assertEqual(mock_record_audit.call_args.kwargs["action"], "github_import_disabled")


if __name__ == "__main__":
    unittest.main()
