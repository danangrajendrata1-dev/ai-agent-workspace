import unittest
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.services.github_import_service import (
    approve_github_skill_import,
    disable_github_import,
    import_selected_github_skill,
    preview_github_skill,
    reject_github_import,
)
from app.services.skill_service import attach_imported_skill_to_agent


def build_agent(owner_id: uuid.UUID):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name="Agent One",
        slug="agent-one",
        description="",
        role_description="Helpful agent",
        default_model_provider_id=None,
        default_model_name=None,
        status="active",
        max_steps=10,
        max_runtime_seconds=300,
        max_token_budget=None,
        requires_approval_by_default=True,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


def build_skill(*, source_id: uuid.UUID, status: str = "inactive"):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        name="Imported Skill",
        slug="imported-skill",
        description="Imported skill",
        content="Imported skill content",
        source_type="github",
        source_id=source_id,
        version_label="1.0.0",
        risk_level="low",
        status=status,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


def build_import_record(*, import_id: uuid.UUID, owner_id: uuid.UUID, status: str = "preview"):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=import_id,
        owner_id=owner_id,
        repo_url="https://github.com/example/repo",
        branch="main",
        commit_sha=None,
        import_type="skill",
        file_path="skills/example/SKILL.md",
        content_preview='{"name":"Email Summary","version":"1.0.0","description":"Generate summary."}',
        status=status,
        review_notes=None,
        created_at=now,
        updated_at=now,
    )


def build_assignment(agent_id: uuid.UUID, skill):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        agent_id=agent_id,
        skill_id=skill.id,
        is_enabled=True,
        created_at=now,
        skill=skill,
    )


class GitHubImportOwnershipLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.owner_id = uuid.uuid4()
        self.other_owner_id = uuid.uuid4()
        self.import_id = uuid.uuid4()
        self.agent = build_agent(self.owner_id)
        self.skill = build_skill(source_id=self.import_id)
        self.assignment = build_assignment(self.agent.id, self.skill)
        self.preview_payload = SimpleNamespace(
            repo_url="https://github.com/example/repo",
            branch="main",
            file_path="SKILL.md",
        )
        self.selected_payload = SimpleNamespace(
            repo_url="https://github.com/example/repo",
            branch="main",
            skill_path="skills/pdf",
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

    def test_preview_persists_owner_id(self):
        github_import = build_import_record(import_id=self.import_id, owner_id=self.owner_id)

        with patch(
            "app.services.github_import_service.fetch_text_preview",
            return_value=SimpleNamespace(
                raw_url="https://raw.githubusercontent.com/example/repo/main/SKILL.md",
                content=github_import.content_preview,
                commit_sha=None,
                source_identity=None,
                source_identity_type=None,
            ),
        ), patch(
            "app.services.github_import_service.github_import_repository.create_preview",
            return_value=github_import,
        ) as mock_create_preview, patch(
            "app.services.github_import_service.log_service.record_activity"
        ):
            result = preview_github_skill(self.db, self.preview_payload, owner_id=self.owner_id)

        self.assertEqual(result.status, "preview")
        self.assertEqual(mock_create_preview.call_args.args[1]["owner_id"], self.owner_id)

    def test_selected_collection_import_persists_owner_id(self):
        github_import = build_import_record(import_id=self.import_id, owner_id=self.owner_id)

        with patch(
            "app.services.github_import_service.fetch_text_preview",
            return_value=SimpleNamespace(
                raw_url="https://raw.githubusercontent.com/example/repo/main/skills/pdf/SKILL.md",
                content=github_import.content_preview,
                commit_sha=None,
                source_identity=None,
                source_identity_type=None,
            ),
        ), patch(
            "app.services.github_import_service.github_import_repository.create_preview",
            return_value=github_import,
        ) as mock_create_preview, patch(
            "app.services.github_import_service.log_service.record_activity"
        ):
            result = import_selected_github_skill(self.db, self.selected_payload, owner_id=self.owner_id)

        self.assertEqual(result.status, "preview")
        self.assertEqual(mock_create_preview.call_args.args[1]["owner_id"], self.owner_id)

    def test_owner_can_approve_reject_and_disable_import(self):
        github_import = build_import_record(import_id=self.import_id, owner_id=self.owner_id)
        approved_import = build_import_record(import_id=self.import_id, owner_id=self.owner_id, status="imported")
        skill = SimpleNamespace(id=uuid.uuid4(), status="inactive")

        with patch(
            "app.services.github_import_service.github_import_repository.get_by_id_for_owner",
            return_value=github_import,
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
        ), patch(
            "app.services.github_import_service.assess_skill_manifest_risk",
            return_value=SimpleNamespace(
                risk_level="low",
                reasons=["Metadata-only manifest."],
                requires_review=False,
                is_blocked=False,
            ),
        ), patch(
            "app.services.github_import_service.ensure_unique_skill_slug",
            return_value="email-summary",
        ), patch(
            "app.services.github_import_service.skill_repository.create",
            return_value=skill,
        ) as mock_create_skill, patch(
            "app.services.github_import_service.github_import_repository.update_status"
        ) as mock_update_status, patch(
            "app.services.github_import_service.github_import_repository.update_review_notes"
        ) as mock_update_review_notes, patch(
            "app.services.github_import_service.serialize_github_import",
            return_value=approved_import,
        ):
            approve_result = approve_github_skill_import(
                self.db,
                self.import_id,
                self.approve_payload,
                owner_id=self.owner_id,
            )

        self.assertEqual(approve_result.status, "imported")
        self.assertEqual(mock_create_skill.call_args.args[1]["status"], "inactive")
        self.assertEqual(mock_update_status.call_args.args[2], "imported")
        mock_update_review_notes.assert_called_once_with(self.db, github_import, "reviewed")

        with patch(
            "app.services.github_import_service.github_import_repository.get_by_id_for_owner",
            return_value=github_import,
        ), patch(
            "app.services.github_import_service.github_import_repository.update_status"
        ) as mock_reject_status, patch(
            "app.services.github_import_service.github_import_repository.update_review_notes"
        ) as mock_reject_review_notes, patch(
            "app.services.github_import_service.serialize_github_import",
            return_value=build_import_record(import_id=self.import_id, owner_id=self.owner_id, status="rejected"),
        ):
            reject_result = reject_github_import(
                self.db,
                self.import_id,
                SimpleNamespace(review_notes="not approved"),
                owner_id=self.owner_id,
            )

        self.assertEqual(reject_result.status, "rejected")
        self.assertEqual(mock_reject_status.call_args.args[2], "rejected")
        mock_reject_review_notes.assert_called_once_with(self.db, github_import, "not approved")

        with patch(
            "app.services.github_import_service.github_import_repository.get_by_id_for_owner",
            return_value=github_import,
        ), patch(
            "app.services.github_import_service.github_import_repository.update_status"
        ) as mock_disable_status, patch(
            "app.services.github_import_service.serialize_github_import",
            return_value=build_import_record(import_id=self.import_id, owner_id=self.owner_id, status="disabled"),
        ):
            disable_result = disable_github_import(
                self.db,
                self.import_id,
                owner_id=self.owner_id,
            )

        self.assertEqual(disable_result.status, "disabled")
        self.assertEqual(mock_disable_status.call_args.args[2], "disabled")

    def test_non_owner_cannot_process_import(self):
        with patch(
            "app.services.github_import_service.github_import_repository.get_by_id_for_owner",
            return_value=None,
        ), patch(
            "app.services.github_import_service.github_import_repository.get_by_id",
            side_effect=AssertionError("owner lookup should be enforced"),
        ):
            for action in (
                lambda: approve_github_skill_import(
                    self.db,
                    self.import_id,
                    self.approve_payload,
                    owner_id=self.other_owner_id,
                ),
                lambda: reject_github_import(
                    self.db,
                    self.import_id,
                    SimpleNamespace(review_notes="nope"),
                    owner_id=self.other_owner_id,
                ),
                lambda: disable_github_import(
                    self.db,
                    self.import_id,
                    owner_id=self.other_owner_id,
                ),
            ):
                with self.subTest(action=action):
                    with self.assertRaises(HTTPException) as exc_info:
                        action()
                    self.assertEqual(exc_info.exception.status_code, 404)

    def test_pending_rejected_and_disabled_imports_cannot_be_attached(self):
        for status in ("preview", "rejected", "disabled"):
            with self.subTest(status=status):
                github_import = build_import_record(
                    import_id=self.import_id,
                    owner_id=self.owner_id,
                    status=status,
                )
                with patch(
                    "app.services.skill_service.agent_repository.get_by_id",
                    return_value=self.agent,
                ), patch(
                    "app.services.skill_service.skill_repository.get_by_id",
                    return_value=self.skill,
                ), patch(
                    "app.services.skill_service.github_import_repository.get_by_id_for_owner",
                    return_value=github_import,
                ), patch(
                    "app.services.skill_service.agent_skill_repository.get_assignment",
                    return_value=None,
                ):
                    with self.assertRaises(HTTPException) as exc_info:
                        attach_imported_skill_to_agent(
                            self.db,
                            owner_id=self.owner_id,
                            agent_id=self.agent.id,
                            skill_id=self.skill.id,
                            current_user=SimpleNamespace(role="user"),
                        )

                self.assertEqual(exc_info.exception.status_code, 400)
                self.assertIn("blocked", str(exc_info.exception.detail).lower())

    def test_approved_import_can_be_attached(self):
        github_import = build_import_record(
            import_id=self.import_id,
            owner_id=self.owner_id,
            status="imported",
        )
        assignment = build_assignment(self.agent.id, self.skill)

        with patch(
            "app.services.skill_service.agent_repository.get_by_id",
            return_value=self.agent,
        ), patch(
            "app.services.skill_service.skill_repository.get_by_id",
            return_value=self.skill,
        ), patch(
            "app.services.skill_service.github_import_repository.get_by_id_for_owner",
            return_value=github_import,
        ), patch(
            "app.services.skill_service.agent_skill_repository.get_assignment",
            side_effect=[None, assignment],
        ), patch(
            "app.services.skill_service.agent_skill_repository.assign_skill_to_agent",
            return_value=assignment,
        ):
            result = attach_imported_skill_to_agent(
                self.db,
                owner_id=self.owner_id,
                agent_id=self.agent.id,
                skill_id=self.skill.id,
                current_user=SimpleNamespace(role="user"),
            )

        self.assertTrue(result.is_enabled)
        self.assertEqual(result.skill.import_status, "imported")

    def test_other_owner_import_cannot_be_attached(self):
        with patch(
            "app.services.skill_service.agent_repository.get_by_id",
            return_value=self.agent,
        ), patch(
            "app.services.skill_service.skill_repository.get_by_id",
            return_value=self.skill,
        ), patch(
            "app.services.skill_service.github_import_repository.get_by_id_for_owner",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as exc_info:
                attach_imported_skill_to_agent(
                    self.db,
                    owner_id=self.owner_id,
                    agent_id=self.agent.id,
                    skill_id=self.skill.id,
                    current_user=SimpleNamespace(role="user"),
                )

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertIn("metadata", str(exc_info.exception.detail).lower())


if __name__ == "__main__":
    unittest.main()
