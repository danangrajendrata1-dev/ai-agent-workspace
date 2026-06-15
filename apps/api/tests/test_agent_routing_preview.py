import unittest
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from app.services.agent_routing_service import preview_agent_routing


def build_agent(*, owner_id: uuid.UUID, name: str, description: str, role_description: str):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name=name,
        slug=name.lower().replace(" ", "-"),
        description=description,
        role_description=role_description,
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


def build_active_skill(*, title: str, skill_type: str = "prompt_skill"):
    now = datetime.now(UTC)
    skill_id = uuid.uuid4()
    skill = SimpleNamespace(
        id=skill_id,
        skill_id=skill_id,
        title=title,
        skill_type=skill_type,
        status="active",
        security_status="safe",
        matched_terms=[],
        match_score=0,
        reason="",
        source_url=None,
        source_reference=None,
        source_branch=None,
        file_path=None,
        import_status="manual",
        risk_level="low",
        warnings=[],
        resource_references=[],
        created_at=now,
        is_attachable=True,
        attach_block_reason=None,
    )
    assignment = SimpleNamespace(
        id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        skill_id=skill_id,
        is_enabled=True,
        created_at=now,
        skill=skill,
    )
    return assignment


class AgentRoutingPreviewTest(unittest.TestCase):
    def setUp(self):
        self.db = SimpleNamespace()
        self.user_id = uuid.uuid4()
        self.other_user_id = uuid.uuid4()

    def test_user_can_preview_routing_across_own_agents(self):
        summarize_agent = build_agent(
            owner_id=self.user_id,
            name="Document Summarization",
            description="Summarize documents and answer questions.",
            role_description="Helpful research and summarization agent.",
        )
        workflow_agent = build_agent(
            owner_id=self.user_id,
            name="Workflow Pilot",
            description="Automate routine workspace tasks.",
            role_description="Workflow and operations assistant.",
        )
        summarize_skill = build_active_skill(title="Document Summarization", skill_type="knowledge_skill")
        workflow_skill = build_active_skill(title="Weekly Workflow", skill_type="workflow_skill")

        def list_active_skills_side_effect(*args, **kwargs):
            agent_id = kwargs["agent_id"]
            if agent_id == summarize_agent.id:
                return [summarize_skill]
            if agent_id == workflow_agent.id:
                return [workflow_skill]
            return []

        with patch(
            "app.services.agent_routing_service.agent_repository.list_by_owner",
            return_value=[summarize_agent, workflow_agent],
        ), patch(
            "app.services.agent_routing_service.skill_service.list_active_agent_skills",
            side_effect=list_active_skills_side_effect,
        ):
            result = preview_agent_routing(
                self.db,
                current_user=SimpleNamespace(id=self.user_id, role="user"),
                task_text="Please do document summarization for this report.",
            )

        self.assertEqual(result.confidence, "high")
        self.assertIsNotNone(result.recommended_agent)
        self.assertEqual(result.recommended_agent.name, "Document Summarization")
        self.assertGreaterEqual(len(result.candidate_agents), 2)
        self.assertTrue(any("document" in reason.lower() for reason in result.reasons))
        self.assertTrue(result.active_skill_matches)
        self.assertEqual(result.active_skill_matches[0].title, "Document Summarization")

    def test_low_confidence_when_no_clear_match(self):
        agent_one = build_agent(
            owner_id=self.user_id,
            name="General Assistant",
            description="General workspace helper.",
            role_description="Helpful workspace assistant.",
        )
        agent_two = build_agent(
            owner_id=self.user_id,
            name="Ops Assistant",
            description="Operations helper.",
            role_description="Ops and admin support.",
        )

        with patch(
            "app.services.agent_routing_service.agent_repository.list_by_owner",
            return_value=[agent_one, agent_two],
        ), patch(
            "app.services.agent_routing_service.skill_service.list_active_agent_skills",
            return_value=[],
        ):
            result = preview_agent_routing(
                self.db,
                current_user=SimpleNamespace(id=self.user_id, role="user"),
                task_text="Please plan a surprise party.",
            )

        self.assertEqual(result.confidence, "low")
        self.assertIsNotNone(result.recommended_agent)
        self.assertIn("choose an agent manually", result.note.lower())

    def test_user_cannot_route_against_another_users_agents(self):
        own_agent = build_agent(
            owner_id=self.user_id,
            name="Own Agent",
            description="Own workspace helper.",
            role_description="Own workspace assistant.",
        )
        other_agent = build_agent(
            owner_id=self.other_user_id,
            name="Other Agent",
            description="Other workspace helper.",
            role_description="Other workspace assistant.",
        )

        with patch(
            "app.services.agent_routing_service.agent_repository.list_by_owner",
            return_value=[own_agent],
        ) as mock_list_by_owner, patch(
            "app.services.agent_routing_service.agent_repository.list_all_active",
            return_value=[own_agent, other_agent],
        ) as mock_list_all, patch(
            "app.services.agent_routing_service.skill_service.list_active_agent_skills",
            return_value=[],
        ):
            result = preview_agent_routing(
                self.db,
                current_user=SimpleNamespace(id=self.user_id, role="user"),
                task_text="general task",
            )

        mock_list_by_owner.assert_called_once()
        mock_list_all.assert_not_called()
        self.assertEqual(len(result.candidate_agents), 1)
        self.assertEqual(result.candidate_agents[0].name, "Own Agent")
        self.assertFalse(any(candidate.name == "Other Agent" for candidate in result.candidate_agents))

    def test_admin_can_route_across_all_agents(self):
        admin_agent = build_agent(
            owner_id=self.other_user_id,
            name="Admin Research",
            description="Research and summary helper.",
            role_description="Research support agent.",
        )
        second_agent = build_agent(
            owner_id=self.user_id,
            name="Workflow Ops",
            description="Workflow automation helper.",
            role_description="Operations and automation agent.",
        )

        with patch(
            "app.services.agent_routing_service.agent_repository.list_all_active",
            return_value=[admin_agent, second_agent],
        ) as mock_list_all, patch(
            "app.services.agent_routing_service.skill_service.list_active_agent_skills",
            return_value=[],
        ):
            result = preview_agent_routing(
                self.db,
                current_user=SimpleNamespace(id=self.user_id, role="admin"),
                task_text="summarize research notes",
            )

        mock_list_all.assert_called_once()
        self.assertEqual(len(result.candidate_agents), 2)
        self.assertTrue(any(candidate.name == "Admin Research" for candidate in result.candidate_agents))
        self.assertTrue(any(candidate.name == "Workflow Ops" for candidate in result.candidate_agents))

    def test_preview_response_does_not_expose_secrets_or_content(self):
        agent = build_agent(
            owner_id=self.user_id,
            name="Safe Agent",
            description="Safe helper.",
            role_description="Safe workspace assistant.",
        )

        with patch(
            "app.services.agent_routing_service.agent_repository.list_by_owner",
            return_value=[agent],
        ), patch(
            "app.services.agent_routing_service.skill_service.list_active_agent_skills",
            return_value=[],
        ):
            result = preview_agent_routing(
                self.db,
                current_user=SimpleNamespace(id=self.user_id, role="user"),
                task_text="safe task",
            )

        self.assertFalse(hasattr(result.recommended_agent, "owner_id"))
        self.assertFalse(hasattr(result.recommended_agent, "content"))
        self.assertFalse(hasattr(result.recommended_agent, "api_key"))
        self.assertFalse(hasattr(result.recommended_agent, "token"))
        self.assertFalse(hasattr(result.recommended_agent, "password"))


if __name__ == "__main__":
    unittest.main()
