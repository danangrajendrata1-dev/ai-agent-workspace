import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.integrations.github_client import GitHubPreviewFetchResult
from app.services.github_import_service import approve_github_skill_import, preview_github_skill


class GitHubImportSourceConsistencyTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.import_id = uuid.uuid4()
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

    def _create_preview_side_effect(self, *args, **kwargs):
        if len(args) >= 2 and isinstance(args[1], dict):
            data = args[1]
        else:
            data = kwargs
        return SimpleNamespace(
            id=self.import_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **data,
        )

    def test_preview_persists_commit_sha_and_source_identity(self):
        fetch_result = GitHubPreviewFetchResult(
            raw_url="https://raw.githubusercontent.com/example/repo/abc1234/SKILL.md",
            content='{"name":"Email Summary","version":"1.0.0","description":"Generate summary."}',
            commit_sha="abc1234",
            source_identity="abc1234",
            source_identity_type="commit_sha",
        )

        with patch(
            "app.services.github_import_service.fetch_text_preview",
            return_value=fetch_result,
        ), patch(
            "app.services.github_import_service.github_import_repository.create_preview",
            side_effect=self._create_preview_side_effect,
        ) as mock_create_preview, patch(
            "app.services.github_import_service.log_service.record_activity"
        ) as mock_record_activity:
            result = preview_github_skill(self.db, self.preview_payload)

        self.assertEqual(result.commit_sha, "abc1234")
        mock_create_preview.assert_called_once()
        created_payload = mock_create_preview.call_args.args[1]
        self.assertEqual(created_payload["commit_sha"], "abc1234")
        self.assertEqual(created_payload["content_preview"], fetch_result.content)
        self.assertEqual(mock_record_activity.call_args.kwargs["metadata_json"]["commit_sha"], "abc1234")
        self.assertEqual(mock_record_activity.call_args.kwargs["metadata_json"]["source_identity"], "abc1234")
        self.assertEqual(
            mock_record_activity.call_args.kwargs["metadata_json"]["source_identity_type"],
            "commit_sha",
        )

    def test_preview_logs_etag_source_identity_when_commit_sha_unavailable(self):
        fetch_result = GitHubPreviewFetchResult(
            raw_url="https://raw.githubusercontent.com/example/repo/main/SKILL.md",
            content='{"name":"Email Summary","version":"1.0.0","description":"Generate summary."}',
            commit_sha=None,
            source_identity='W/"etag-value"',
            source_identity_type="etag",
        )

        with patch(
            "app.services.github_import_service.fetch_text_preview",
            return_value=fetch_result,
        ), patch(
            "app.services.github_import_service.github_import_repository.create_preview",
            side_effect=self._create_preview_side_effect,
        ) as mock_create_preview, patch(
            "app.services.github_import_service.log_service.record_activity"
        ) as mock_record_activity:
            result = preview_github_skill(self.db, self.preview_payload)

        self.assertIsNone(result.commit_sha)
        created_payload = mock_create_preview.call_args.args[1]
        self.assertIsNone(created_payload["commit_sha"])
        self.assertEqual(
            mock_record_activity.call_args.kwargs["metadata_json"]["source_identity_type"],
            "etag",
        )
        self.assertEqual(
            mock_record_activity.call_args.kwargs["metadata_json"]["source_identity"],
            'W/"etag-value"',
        )

    def test_approve_uses_saved_preview_content_without_refetching_github(self):
        with patch(
            "app.services.github_import_service.github_import_repository.get_by_id",
            return_value=self.github_import,
        ), patch(
            "app.services.github_import_service.fetch_text_preview",
            side_effect=AssertionError("approve must not refetch GitHub content"),
        ), patch(
            "app.services.github_import_service.inspect_skill_manifest_content",
            return_value=SimpleNamespace(
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
            ),
        ), patch("app.services.github_import_service.assess_skill_manifest_risk") as mock_assess, patch(
            "app.services.github_import_service.ensure_unique_skill_slug",
            return_value="email-summary",
        ), patch(
            "app.services.github_import_service.skill_repository.create",
            return_value=SimpleNamespace(id=uuid.uuid4(), status="inactive"),
        ) as mock_create, patch(
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
            result = approve_github_skill_import(self.db, self.import_id, self.approve_payload)

        self.assertEqual(result.status, "imported")
        mock_create.assert_called_once()
        created_payload = mock_create.call_args.args[1]
        self.assertEqual(created_payload["content"], self.github_import.content_preview)
        self.assertEqual(created_payload["status"], "inactive")
        self.assertEqual(mock_update_status.call_args.args[2], "imported")
        mock_update_review_notes.assert_called_once()


if __name__ == "__main__":
    unittest.main()
