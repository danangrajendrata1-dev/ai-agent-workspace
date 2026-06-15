import uuid
import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.schemas.agent import AgentCreate
from app.services.agent_service import create_agent


def build_agent_payload(name: str = "Agent One") -> AgentCreate:
    return AgentCreate(
        name=name,
        slug=None,
        description="Test agent",
        role_description="Helpful workspace agent",
        default_model_provider_id=None,
        default_model_name=None,
        status="active",
        max_steps=10,
        max_runtime_seconds=300,
        max_token_budget=None,
        requires_approval_by_default=True,
        instruction_text="Follow safe workspace rules.",
    )


def build_created_agent(owner_id: uuid.UUID, *, name: str, slug: str) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name=name,
        slug=slug,
        description="Test agent",
        role_description="Helpful workspace agent",
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


class AgentQuotaTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.owner_id = uuid.uuid4()

    def test_free_user_can_create_up_to_five_agents(self):
        created_agents = [
            build_created_agent(self.owner_id, name=f"Agent {index + 1}", slug=f"agent-{index + 1}")
            for index in range(5)
        ]

        with (
            patch("app.services.agent_service.user_repository.get_by_id", return_value=SimpleNamespace(
                id=self.owner_id,
                role="user",
                subscription_plan="free",
                is_active=True,
                deleted_at=None,
            )),
            patch("app.services.agent_service.validate_default_model_provider"),
            patch("app.services.agent_service.ensure_unique_slug", side_effect=[
                "agent-1",
                "agent-2",
                "agent-3",
                "agent-4",
                "agent-5",
            ]),
            patch("app.services.agent_service.agent_repository.count_by_owner", side_effect=[0, 1, 2, 3, 4]),
            patch("app.services.agent_service.agent_repository.create", side_effect=created_agents) as mock_create,
            patch("app.services.agent_service.agent_instruction_repository.create_instruction"),
            patch("app.services.agent_service.serialize_agent", side_effect=lambda agent: agent),
        ):
            for index in range(5):
                result = create_agent(self.db, owner_id=self.owner_id, payload=build_agent_payload(f"Agent {index + 1}"))
                self.assertEqual(result.name, f"Agent {index + 1}")

        self.assertEqual(mock_create.call_count, 5)

    def test_free_user_cannot_create_sixth_agent(self):
        created_agent = build_created_agent(self.owner_id, name="Agent 6", slug="agent-6")

        with patch("app.services.agent_service.user_repository.get_by_id", return_value=SimpleNamespace(
            id=self.owner_id,
            role="user",
            subscription_plan="free",
            is_active=True,
            deleted_at=None,
        )), patch(
            "app.services.agent_service.validate_default_model_provider"
        ), patch("app.services.agent_service.ensure_unique_slug", return_value="agent-6"), patch(
            "app.services.agent_service.agent_repository.count_by_owner",
            return_value=5,
        ), patch("app.services.agent_service.agent_repository.create", return_value=created_agent) as mock_create, patch(
            "app.services.agent_service.agent_instruction_repository.create_instruction"
        ):
            with self.assertRaises(HTTPException) as exc_info:
                create_agent(self.db, owner_id=self.owner_id, payload=build_agent_payload("Agent 6"))

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertIn("Your Free plan allows up to 5 agents", exc_info.exception.detail)
        mock_create.assert_not_called()

    def test_pro_limit_uses_ten_agents(self):
        created_agent = build_created_agent(self.owner_id, name="Pro Agent", slug="pro-agent")

        with patch("app.services.agent_service.user_repository.get_by_id", return_value=SimpleNamespace(
            id=self.owner_id,
            role="user",
            subscription_plan="pro",
            is_active=True,
            deleted_at=None,
        )), patch(
            "app.services.agent_service.validate_default_model_provider"
        ), patch("app.services.agent_service.ensure_unique_slug", return_value="pro-agent"), patch(
            "app.services.agent_service.agent_repository.count_by_owner",
            return_value=9,
        ), patch("app.services.agent_service.agent_repository.create", return_value=created_agent) as mock_create, patch(
            "app.services.agent_service.agent_instruction_repository.create_instruction"
        ), patch("app.services.agent_service.serialize_agent", return_value=created_agent):
            result = create_agent(self.db, owner_id=self.owner_id, payload=build_agent_payload("Pro Agent"))

        self.assertEqual(result, created_agent)
        mock_create.assert_called_once()

        with patch("app.services.agent_service.user_repository.get_by_id", return_value=SimpleNamespace(
            id=self.owner_id,
            role="user",
            subscription_plan="pro",
            is_active=True,
            deleted_at=None,
        )), patch(
            "app.services.agent_service.validate_default_model_provider"
        ), patch("app.services.agent_service.ensure_unique_slug", return_value="pro-agent-2"), patch(
            "app.services.agent_service.agent_repository.count_by_owner",
            return_value=10,
        ), patch("app.services.agent_service.agent_repository.create", return_value=created_agent) as blocked_create, patch(
            "app.services.agent_service.agent_instruction_repository.create_instruction"
        ):
            with self.assertRaises(HTTPException) as exc_info:
                create_agent(self.db, owner_id=self.owner_id, payload=build_agent_payload("Pro Agent 2"))

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertIn("Your Pro plan allows up to 10 agents", exc_info.exception.detail)
        blocked_create.assert_not_called()

    def test_executive_limit_uses_fifty_agents(self):
        created_agent = build_created_agent(self.owner_id, name="Executive Agent", slug="executive-agent")

        with patch("app.services.agent_service.user_repository.get_by_id", return_value=SimpleNamespace(
            id=self.owner_id,
            role="user",
            subscription_plan="executive",
            is_active=True,
            deleted_at=None,
        )), patch(
            "app.services.agent_service.validate_default_model_provider"
        ), patch("app.services.agent_service.ensure_unique_slug", return_value="executive-agent"), patch(
            "app.services.agent_service.agent_repository.count_by_owner",
            return_value=49,
        ), patch("app.services.agent_service.agent_repository.create", return_value=created_agent) as mock_create, patch(
            "app.services.agent_service.agent_instruction_repository.create_instruction"
        ), patch("app.services.agent_service.serialize_agent", return_value=created_agent):
            result = create_agent(self.db, owner_id=self.owner_id, payload=build_agent_payload("Executive Agent"))

        self.assertEqual(result, created_agent)
        mock_create.assert_called_once()

        with patch("app.services.agent_service.user_repository.get_by_id", return_value=SimpleNamespace(
            id=self.owner_id,
            role="user",
            subscription_plan="executive",
            is_active=True,
            deleted_at=None,
        )), patch(
            "app.services.agent_service.validate_default_model_provider"
        ), patch("app.services.agent_service.ensure_unique_slug", return_value="executive-agent-2"), patch(
            "app.services.agent_service.agent_repository.count_by_owner",
            return_value=50,
        ), patch("app.services.agent_service.agent_repository.create", return_value=created_agent) as blocked_create, patch(
            "app.services.agent_service.agent_instruction_repository.create_instruction"
        ):
            with self.assertRaises(HTTPException) as exc_info:
                create_agent(self.db, owner_id=self.owner_id, payload=build_agent_payload("Executive Agent 2"))

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertIn("Your Executive plan allows up to 50 agents", exc_info.exception.detail)
        blocked_create.assert_not_called()

    def test_admin_bypasses_agent_limit(self):
        created_agent = build_created_agent(self.owner_id, name="Admin Agent", slug="admin-agent")

        with patch("app.services.agent_service.user_repository.get_by_id", return_value=SimpleNamespace(
            id=self.owner_id,
            role="admin",
            subscription_plan="free",
            is_active=True,
            deleted_at=None,
        )), patch(
            "app.services.agent_service.validate_default_model_provider"
        ), patch("app.services.agent_service.ensure_unique_slug", return_value="admin-agent"), patch(
            "app.services.agent_service.agent_repository.count_by_owner"
        ) as mock_count, patch("app.services.agent_service.agent_repository.create", return_value=created_agent) as mock_create, patch(
            "app.services.agent_service.agent_instruction_repository.create_instruction"
        ), patch("app.services.agent_service.serialize_agent", return_value=created_agent):
            result = create_agent(self.db, owner_id=self.owner_id, payload=build_agent_payload("Admin Agent"))

        self.assertEqual(result, created_agent)
        mock_count.assert_not_called()
        mock_create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
