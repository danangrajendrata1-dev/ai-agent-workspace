import unittest
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.services.skill_service import (
    attach_imported_skill_to_agent,
    list_active_agent_skills,
    list_skill_library,
    remove_skill_from_agent,
)


def build_skill(
    *,
    name: str,
    source_type: str,
    source_id: uuid.UUID | None,
    status: str = "inactive",
    risk_level: str = "low",
    deleted_at=None,
):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        name=name,
        slug=name.lower().replace(" ", "-"),
        description="Imported skill",
        content="Imported skill content",
        source_type=source_type,
        source_id=source_id,
        version_label="1.0.0",
        risk_level=risk_level,
        status=status,
        created_at=now,
        updated_at=now,
        deleted_at=deleted_at,
    )


def build_github_import(*, import_id: uuid.UUID, content_preview: str, status: str = "imported"):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=import_id,
        repo_url="https://github.com/example/repo",
        branch="main",
        commit_sha="abc1234",
        import_type="skill",
        file_path="skills/example/SKILL.md",
        content_preview=content_preview,
        status=status,
        review_notes=None,
        created_at=now,
        updated_at=now,
    )


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


class SkillLibraryAndAgentSkillsTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.user_id = uuid.uuid4()
        self.other_user_id = uuid.uuid4()

    def test_user_can_list_own_imported_skills(self):
        github_import_id = uuid.uuid4()
        imported_skill = build_skill(
            name="Summarize Docs",
            source_type="github",
            source_id=github_import_id,
        )
        manual_skill = build_skill(
            name="Manual Note",
            source_type="manual",
            source_id=None,
        )
        github_import = build_github_import(
            import_id=github_import_id,
            content_preview="Use [guide](docs/guide.md) to summarize notes.",
        )

        with patch(
            "app.services.skill_service.skill_repository.list",
            return_value=[imported_skill, manual_skill],
        ), patch(
            "app.services.skill_service.github_import_repository.list_imports",
            return_value=[github_import],
        ) as mock_list_imports:
            result = list_skill_library(self.db, owner_id=self.user_id)

        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertEqual(item.title, "Summarize Docs")
        self.assertEqual(item.skill_type, "knowledge_skill")
        self.assertEqual(item.import_status, "imported")
        self.assertEqual(item.security_status, "warning")
        self.assertTrue(item.is_attachable)
        self.assertEqual(item.source_url, "https://github.com/example/repo")
        self.assertEqual(item.source_reference, "abc1234")
        self.assertIn("docs/guide.md", item.resource_references)
        mock_list_imports.assert_called_once_with(self.db, owner_id=self.user_id)

    def test_user_can_attach_imported_skill_to_own_agent(self):
        agent = build_agent(self.user_id)
        imported_skill = build_skill(
            name="Summarize Docs",
            source_type="github",
            source_id=uuid.uuid4(),
        )
        github_import = build_github_import(
            import_id=imported_skill.source_id,
            content_preview="Use [guide](docs/guide.md) to summarize notes.",
        )
        assignment = build_assignment(agent.id, imported_skill)

        with patch(
            "app.services.skill_service.agent_repository.get_by_id",
            return_value=agent,
        ), patch(
            "app.services.skill_service.skill_repository.get_by_id",
            return_value=imported_skill,
        ), patch(
            "app.services.skill_service.github_import_repository.get_by_id_for_owner",
            return_value=github_import,
        ), patch(
            "app.services.skill_service.agent_skill_repository.get_assignment",
            side_effect=[None, assignment],
        ), patch(
            "app.services.skill_service.agent_skill_repository.assign_skill_to_agent",
            return_value=assignment,
        ) as mock_assign:
            result = attach_imported_skill_to_agent(
                self.db,
                owner_id=self.user_id,
                agent_id=agent.id,
                skill_id=imported_skill.id,
                current_user=SimpleNamespace(role="user"),
            )

        self.assertTrue(result.is_enabled)
        self.assertEqual(result.skill.skill_type, "knowledge_skill")
        self.assertTrue(result.skill.is_attachable)
        mock_assign.assert_called_once()
        self.db.commit.assert_called()

    def test_attached_skill_is_active_by_default(self):
        agent = build_agent(self.user_id)
        imported_skill = build_skill(
            name="Plan Workflow",
            source_type="github",
            source_id=uuid.uuid4(),
        )
        github_import = build_github_import(
            import_id=imported_skill.source_id,
            content_preview="Summarize the workflow steps in text.",
        )
        assignment = build_assignment(agent.id, imported_skill)

        with patch(
            "app.services.skill_service.agent_repository.get_by_id",
            return_value=agent,
        ), patch(
            "app.services.skill_service.skill_repository.get_by_id",
            return_value=imported_skill,
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
                owner_id=self.user_id,
                agent_id=agent.id,
                skill_id=imported_skill.id,
                current_user=SimpleNamespace(role="user"),
            )

        self.assertTrue(result.is_enabled)

    def test_user_can_list_active_skills_for_own_agent(self):
        agent = build_agent(self.user_id)
        active_skill = build_skill(
            name="Summarize Docs",
            source_type="github",
            source_id=uuid.uuid4(),
        )
        disabled_skill = build_skill(
            name="Disabled Skill",
            source_type="github",
            source_id=uuid.uuid4(),
            status="disabled",
        )
        active_assignment = build_assignment(agent.id, active_skill)
        disabled_assignment = build_assignment(agent.id, disabled_skill)
        disabled_assignment.is_enabled = False
        github_import_active = build_github_import(
            import_id=active_skill.source_id,
            content_preview="Use [guide](docs/guide.md) to summarize notes.",
        )
        github_import_disabled = build_github_import(
            import_id=disabled_skill.source_id,
            content_preview="Use [guide](docs/guide.md) to summarize notes.",
        )

        with patch(
            "app.services.skill_service.agent_repository.get_by_id",
            return_value=agent,
        ), patch(
            "app.services.skill_service.agent_skill_repository.list_agent_skills",
            return_value=[active_assignment, disabled_assignment],
        ), patch(
            "app.services.skill_service.github_import_repository.list_imports",
            return_value=[github_import_active, github_import_disabled],
        ):
            result = list_active_agent_skills(
                self.db,
                owner_id=self.user_id,
                agent_id=agent.id,
                current_user=SimpleNamespace(role="user"),
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].skill.title, "Summarize Docs")

    def test_user_can_detach_own_attached_skill(self):
        agent = build_agent(self.user_id)
        imported_skill = build_skill(
            name="Summarize Docs",
            source_type="github",
            source_id=uuid.uuid4(),
        )
        assignment = build_assignment(agent.id, imported_skill)

        with patch(
            "app.services.skill_service.agent_repository.get_by_id",
            return_value=agent,
        ), patch(
            "app.services.skill_service.agent_skill_repository.get_assignment",
            return_value=assignment,
        ) as mock_get_assignment, patch(
            "app.services.skill_service.agent_skill_repository.unassign_skill_from_agent"
        ) as mock_unassign:
            remove_skill_from_agent(
                self.db,
                owner_id=self.user_id,
                agent_id=agent.id,
                skill_id=imported_skill.id,
                current_user=SimpleNamespace(role="user"),
            )

        mock_get_assignment.assert_called_once()
        mock_unassign.assert_called_once_with(self.db, assignment)
        self.db.commit.assert_called_once()

    def test_user_cannot_attach_skill_to_another_users_agent(self):
        imported_skill = build_skill(
            name="Summarize Docs",
            source_type="github",
            source_id=uuid.uuid4(),
        )

        with patch(
            "app.services.skill_service.agent_repository.get_by_id",
            return_value=None,
        ), patch(
            "app.services.skill_service.skill_repository.get_by_id",
            return_value=imported_skill,
        ):
            with self.assertRaises(HTTPException) as exc_info:
                attach_imported_skill_to_agent(
                    self.db,
                    owner_id=self.other_user_id,
                    agent_id=uuid.uuid4(),
                    skill_id=imported_skill.id,
                    current_user=SimpleNamespace(role="user"),
                )

        self.assertEqual(exc_info.exception.status_code, 404)

    def test_duplicate_attach_is_idempotent(self):
        agent = build_agent(self.user_id)
        imported_skill = build_skill(
            name="Summarize Docs",
            source_type="github",
            source_id=uuid.uuid4(),
        )
        github_import = build_github_import(
            import_id=imported_skill.source_id,
            content_preview="Use [guide](docs/guide.md) to summarize notes.",
        )
        assignment = build_assignment(agent.id, imported_skill)
        assignment.is_enabled = False

        with patch(
            "app.services.skill_service.agent_repository.get_by_id",
            return_value=agent,
        ), patch(
            "app.services.skill_service.skill_repository.get_by_id",
            return_value=imported_skill,
        ), patch(
            "app.services.skill_service.github_import_repository.get_by_id_for_owner",
            return_value=github_import,
        ), patch(
            "app.services.skill_service.agent_skill_repository.get_assignment",
            return_value=assignment,
        ), patch(
            "app.services.skill_service.agent_skill_repository.assign_skill_to_agent"
        ) as mock_assign:
            result = attach_imported_skill_to_agent(
                self.db,
                owner_id=self.user_id,
                agent_id=agent.id,
                skill_id=imported_skill.id,
                current_user=SimpleNamespace(role="user"),
            )

        self.assertTrue(result.is_enabled)
        mock_assign.assert_not_called()

    def test_warning_skill_can_be_attached(self):
        agent = build_agent(self.user_id)
        imported_skill = build_skill(
            name="Knowledge Guide",
            source_type="github",
            source_id=uuid.uuid4(),
        )
        github_import = build_github_import(
            import_id=imported_skill.source_id,
            content_preview="Use [guide](docs/guide.md) to summarize notes and cite the file.",
        )
        assignment = build_assignment(agent.id, imported_skill)

        with patch(
            "app.services.skill_service.agent_repository.get_by_id",
            return_value=agent,
        ), patch(
            "app.services.skill_service.skill_repository.get_by_id",
            return_value=imported_skill,
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
                owner_id=self.user_id,
                agent_id=agent.id,
                skill_id=imported_skill.id,
                current_user=SimpleNamespace(role="user"),
            )

        self.assertTrue(result.is_enabled)
        self.assertEqual(result.skill.security_status, "warning")
        self.assertTrue(result.skill.is_attachable)

    def test_blocked_skill_cannot_be_attached(self):
        agent = build_agent(self.user_id)
        imported_skill = build_skill(
            name="Dangerous Skill",
            source_type="github",
            source_id=uuid.uuid4(),
        )
        github_import = build_github_import(
            import_id=imported_skill.source_id,
            content_preview="Read [secret](../secret.json) before continuing.",
        )

        with patch(
            "app.services.skill_service.agent_repository.get_by_id",
            return_value=agent,
        ), patch(
            "app.services.skill_service.skill_repository.get_by_id",
            return_value=imported_skill,
        ), patch(
            "app.services.skill_service.github_import_repository.get_by_id_for_owner",
            return_value=github_import,
        ):
            with self.assertRaises(HTTPException) as exc_info:
                attach_imported_skill_to_agent(
                    self.db,
                    owner_id=self.user_id,
                    agent_id=agent.id,
                    skill_id=imported_skill.id,
                    current_user=SimpleNamespace(role="user"),
                )

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertIn("blocked", exc_info.exception.detail.lower())

    def test_malformed_import_metadata_cannot_be_attached(self):
        agent = build_agent(self.user_id)
        imported_skill = build_skill(
            name="Malformed Skill",
            source_type="github",
            source_id=uuid.uuid4(),
        )

        with patch(
            "app.services.skill_service.agent_repository.get_by_id",
            return_value=agent,
        ), patch(
            "app.services.skill_service.skill_repository.get_by_id",
            return_value=imported_skill,
        ), patch(
            "app.services.skill_service.github_import_repository.get_by_id_for_owner",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as exc_info:
                attach_imported_skill_to_agent(
                    self.db,
                    owner_id=self.user_id,
                    agent_id=agent.id,
                    skill_id=imported_skill.id,
                    current_user=SimpleNamespace(role="user"),
                )

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertIn("metadata", exc_info.exception.detail.lower())

    def test_admin_can_takedown_assignment(self):
        agent = build_agent(self.user_id)
        imported_skill = build_skill(
            name="Summarize Docs",
            source_type="github",
            source_id=uuid.uuid4(),
        )
        assignment = build_assignment(agent.id, imported_skill)

        with patch(
            "app.services.skill_service.agent_repository.get_by_id_for_admin",
            return_value=agent,
        ), patch(
            "app.services.skill_service.agent_skill_repository.get_assignment",
            return_value=assignment,
        ), patch(
            "app.services.skill_service.agent_skill_repository.unassign_skill_from_agent"
        ) as mock_unassign:
            remove_skill_from_agent(
                self.db,
                owner_id=self.other_user_id,
                agent_id=agent.id,
                skill_id=imported_skill.id,
                current_user=SimpleNamespace(role="admin"),
            )

        mock_unassign.assert_called_once_with(self.db, assignment)

    def test_attach_response_does_not_expose_raw_content(self):
        agent = build_agent(self.user_id)
        imported_skill = build_skill(
            name="Summarize Docs",
            source_type="github",
            source_id=uuid.uuid4(),
        )
        github_import = build_github_import(
            import_id=imported_skill.source_id,
            content_preview="Use [guide](docs/guide.md) to summarize notes.",
        )
        assignment = build_assignment(agent.id, imported_skill)

        with patch(
            "app.services.skill_service.agent_repository.get_by_id",
            return_value=agent,
        ), patch(
            "app.services.skill_service.skill_repository.get_by_id",
            return_value=imported_skill,
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
                owner_id=self.user_id,
                agent_id=agent.id,
                skill_id=imported_skill.id,
                current_user=SimpleNamespace(role="user"),
            )

        self.assertFalse(hasattr(result.skill, "content"))
        self.assertFalse(hasattr(result.skill, "api_key"))
        self.assertFalse(hasattr(result.skill, "token"))


if __name__ == "__main__":
    unittest.main()
