import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.services.github_import_service import preview_github_skill


class GitHubImportResponseMetadataTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.import_id = uuid.uuid4()
        self.preview_payload = SimpleNamespace(
            repo_url="https://github.com/example/repo",
            branch="main",
            file_path="SKILL.md",
        )
        self.import_record = SimpleNamespace(
            id=self.import_id,
            repo_url="https://github.com/example/repo",
            branch="main",
            commit_sha="abc1234",
            import_type="skill",
            file_path="SKILL.md",
            content_preview="Use [guide](docs/guide.md) to summarize notes.",
            status="preview",
            review_notes=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def test_preview_response_includes_markdown_resource_metadata(self):
        with patch(
            "app.services.github_import_service.fetch_text_preview",
            return_value=SimpleNamespace(
                raw_url="https://raw.githubusercontent.com/example/repo/main/SKILL.md",
                content=self.import_record.content_preview,
                commit_sha="abc1234",
                source_identity="abc1234",
                source_identity_type="commit_sha",
            ),
        ), patch(
            "app.services.github_import_service.github_import_repository.create_preview",
            return_value=self.import_record,
        ), patch("app.services.github_import_service.log_service.record_activity"):
            result = preview_github_skill(self.db, self.preview_payload)

        self.assertEqual(result.skill_import_type, "markdown_instruction")
        self.assertEqual(result.resource_paths, ["docs/guide.md"])
        self.assertEqual(result.safe_resource_paths, ["docs/guide.md"])
        self.assertEqual(result.risky_resource_paths, [])
        self.assertFalse(result.has_executable_resources)
        self.assertTrue(result.requires_review)
        self.assertTrue(any("no files were fetched or executed" in warning.lower() for warning in result.inspection_warnings))

    def test_preview_response_includes_manifest_metadata(self):
        manifest_content = (
            "{\"name\":\"Email Summary\",\"version\":\"1.0.0\",\"description\":\"Generate summary.\"}"
        )

        with patch(
            "app.services.github_import_service.fetch_text_preview",
            return_value=SimpleNamespace(
                raw_url="https://raw.githubusercontent.com/example/repo/main/SKILL.md",
                content=manifest_content,
                commit_sha=None,
                source_identity=None,
                source_identity_type=None,
            ),
        ), patch(
            "app.services.github_import_service.github_import_repository.create_preview",
            return_value=SimpleNamespace(
                id=self.import_id,
                repo_url="https://github.com/example/repo",
                branch="main",
                commit_sha=None,
                import_type="skill",
                file_path="SKILL.md",
                content_preview=manifest_content,
                status="preview",
                review_notes=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        ), patch("app.services.github_import_service.log_service.record_activity"):
            result = preview_github_skill(self.db, self.preview_payload)

        self.assertEqual(result.skill_import_type, "manifest_skill")
        self.assertEqual(result.resource_paths, [])
        self.assertEqual(result.safe_resource_paths, [])
        self.assertEqual(result.risky_resource_paths, [])
        self.assertEqual(result.blocked_resource_paths, [])
        self.assertFalse(result.has_executable_resources)

    def test_invalid_github_url_is_returned_as_safe_400(self):
        with patch(
            "app.services.github_import_service.fetch_text_preview",
            side_effect=ValueError("GitHub repository URL is invalid."),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                preview_github_skill(self.db, self.preview_payload)

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertIn("invalid", exc_info.exception.detail.lower())

    def test_missing_skill_md_is_returned_as_safe_400(self):
        with patch(
            "app.services.github_import_service.fetch_text_preview",
            side_effect=ValueError("Only SKILL.md files are supported in this step."),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                preview_github_skill(self.db, self.preview_payload)

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertIn("skill.md", exc_info.exception.detail.lower())


if __name__ == "__main__":
    unittest.main()
