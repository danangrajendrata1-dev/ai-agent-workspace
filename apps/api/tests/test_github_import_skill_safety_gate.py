import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.services.github_import_service import approve_github_skill_import


class GitHubImportSkillSafetyGateTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.github_import = SimpleNamespace(
            id="import-id",
            repo_url="https://github.com/example/repo",
            branch="main",
            commit_sha=None,
            import_type="skill",
            file_path="SKILL.md",
            status="preview",
            content_preview='{"name":"Email Summary","version":"1.0.0","description":"Generate summary."}',
            review_notes=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.payload = SimpleNamespace(
            name="Email Summary",
            slug=None,
            description="Generate summary.",
            version_label="1.0.0",
            risk_level="medium",
            status="active",
            review_notes="reviewed",
        )

    def test_unsafe_manifest_blocks_skill_creation(self):
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
        ), patch("app.services.github_import_service.skill_repository.create") as mock_create, patch(
            "app.services.github_import_service.github_import_repository.update_status"
        ) as mock_update_status, patch(
            "app.services.github_import_service.github_import_repository.update_review_notes"
        ) as mock_update_review_notes:
            with self.assertRaises(Exception) as exc_info:
                approve_github_skill_import(self.db, "import-id", self.payload)

        self.assertIn("Skill manifest safety check failed", str(exc_info.exception))
        mock_create.assert_not_called()
        mock_update_status.assert_not_called()
        mock_update_review_notes.assert_not_called()

    def test_safe_manifest_uses_inactive_quarantine_status(self):
        inspection = SimpleNamespace(
            is_safe=True,
            errors=[],
            warnings=["validation warning"],
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
        ), patch("app.services.github_import_service.skill_repository.create") as mock_create, patch(
            "app.services.github_import_service.github_import_repository.update_status"
        ) as mock_update_status, patch(
            "app.services.github_import_service.github_import_repository.update_review_notes"
        ) as mock_update_review_notes, patch(
            "app.services.github_import_service.serialize_github_import",
            return_value=SimpleNamespace(status="imported"),
        ):
            mock_assess.return_value = SimpleNamespace(
                risk_level="low",
                reasons=["Metadata-only manifest."],
                requires_review=False,
                is_blocked=False,
            )
            approve_github_skill_import(self.db, "import-id", self.payload)

        mock_create.assert_called_once()
        created_payload = mock_create.call_args.args[1]
        self.assertEqual(created_payload["status"], "inactive")
        self.assertEqual(created_payload["risk_level"], "low")
        mock_update_status.assert_called_once()
        self.assertEqual(mock_update_status.call_args.args[2], "imported")
        mock_update_review_notes.assert_called_once()

    def test_unsafe_error_does_not_expose_content_preview(self):
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
        ):
            with self.assertRaises(Exception) as exc_info:
                approve_github_skill_import(self.db, "import-id", self.payload)

        self.assertNotIn(self.github_import.content_preview, str(exc_info.exception))


if __name__ == "__main__":
    unittest.main()
