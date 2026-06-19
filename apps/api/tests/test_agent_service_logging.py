import unittest
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.schemas.agent import AgentCreate, AgentUpdate
from app.services.agent_service import create_agent, deactivate_agent, update_agent


def build_agent(owner_id: uuid.UUID, *, name: str = "Agent One", status: str = "active"):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name=name,
        slug=name.lower().replace(" ", "-"),
        description="Helpful agent",
        role_description="Handles workspace tasks.",
        default_model_provider_id=None,
        default_model_name=None,
        status=status,
        max_steps=10,
        max_runtime_seconds=300,
        max_token_budget=None,
        requires_approval_by_default=True,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


class AgentServiceLoggingTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.owner_id = uuid.uuid4()

    def test_create_agent_writes_activity_log(self):
        payload = AgentCreate.model_validate(
            {
                "name": "Agent One",
                "role_description": "Handles workspace tasks.",
                "instruction_text": "Follow safe rules.",
                "status": "active",
                "max_steps": 10,
                "max_runtime_seconds": 300,
                "requires_approval_by_default": True,
            }
        )
        created_agent = build_agent(self.owner_id)

        with patch("app.services.agent_service.user_repository.get_by_id", return_value=SimpleNamespace(role="user", subscription_plan="free")), patch(
            "app.services.agent_service.agent_repository.count_by_owner",
            return_value=0,
        ), patch(
            "app.services.agent_service.validate_default_model_provider"
        ), patch(
            "app.services.agent_service.ensure_unique_slug",
            return_value="agent-one",
        ), patch(
            "app.services.agent_service.agent_repository.create",
            return_value=created_agent,
        ), patch(
            "app.services.agent_service.agent_instruction_repository.create_instruction"
        ), patch(
            "app.services.agent_service.serialize_agent",
            return_value=created_agent,
        ), patch(
            "app.services.agent_service.log_service.record_activity"
        ) as mock_activity:
            result = create_agent(self.db, owner_id=self.owner_id, payload=payload)

        self.assertEqual(result, created_agent)
        self.assertEqual(mock_activity.call_args.kwargs["event_type"], "agent.created")
        self.assertEqual(mock_activity.call_args.kwargs["actor_id"], self.owner_id)
        self.assertNotIn("instruction_text", str(mock_activity.call_args.kwargs))

    def test_update_agent_writes_activity_and_audit_logs(self):
        existing_agent = build_agent(self.owner_id)
        updated_agent = build_agent(self.owner_id, name="Agent Two")
        updated_agent.slug = "agent-two"
        payload = AgentUpdate.model_validate({"name": "Agent Two", "max_steps": 12})

        with patch(
            "app.services.agent_service.agent_repository.get_by_id",
            return_value=existing_agent,
        ), patch(
            "app.services.agent_service.ensure_unique_slug",
            return_value="agent-two",
        ), patch(
            "app.services.agent_service.agent_repository.update",
            return_value=updated_agent,
        ), patch(
            "app.services.agent_service.serialize_agent",
            return_value=updated_agent,
        ), patch(
            "app.services.agent_service.log_service.record_activity"
        ) as mock_activity, patch(
            "app.services.agent_service.log_service.record_audit"
        ) as mock_audit:
            result = update_agent(self.db, owner_id=self.owner_id, agent_id=existing_agent.id, payload=payload)

        self.assertEqual(result, updated_agent)
        self.assertEqual(mock_activity.call_args.kwargs["event_type"], "agent.updated")
        self.assertEqual(mock_audit.call_args.kwargs["action"], "update")
        self.assertEqual(mock_audit.call_args.kwargs["entity_type"], "agent")
        self.assertEqual(mock_audit.call_args.kwargs["before_data"]["name"], "Agent One")
        self.assertEqual(mock_audit.call_args.kwargs["after_data"]["name"], "Agent Two")

    def test_deactivate_agent_writes_activity_and_audit_logs(self):
        existing_agent = build_agent(self.owner_id)
        deactivated_agent = build_agent(self.owner_id, status="inactive")
        deactivated_agent.deleted_at = datetime.now(UTC)

        with patch(
            "app.services.agent_service.agent_repository.get_by_id",
            return_value=existing_agent,
        ), patch(
            "app.services.agent_service.agent_repository.soft_delete",
            return_value=deactivated_agent,
        ), patch(
            "app.services.agent_service.serialize_agent",
            return_value=deactivated_agent,
        ), patch(
            "app.services.agent_service.log_service.record_activity"
        ) as mock_activity, patch(
            "app.services.agent_service.log_service.record_audit"
        ) as mock_audit:
            result = deactivate_agent(self.db, owner_id=self.owner_id, agent_id=existing_agent.id)

        self.assertEqual(result, deactivated_agent)
        self.assertEqual(mock_activity.call_args.kwargs["event_type"], "agent.deactivated")
        self.assertEqual(mock_audit.call_args.kwargs["action"], "deactivate")
        self.assertEqual(mock_audit.call_args.kwargs["entity_type"], "agent")


if __name__ == "__main__":
    unittest.main()
