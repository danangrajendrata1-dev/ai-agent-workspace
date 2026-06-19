import unittest
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.schemas.skill import SkillCreate, SkillUpdate
from app.services.skill_service import create_skill, deactivate_skill, update_skill


def build_skill(*, name: str = "Skill One", status: str = "active"):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        name=name,
        slug=name.lower().replace(" ", "-"),
        description="Helpful skill",
        content="Skill content",
        source_type="manual",
        source_id=None,
        version_label="1.0.0",
        risk_level="low",
        status=status,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


class SkillServiceLoggingTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.owner_id = uuid.uuid4()

    def test_create_skill_writes_activity_log(self):
        payload = SkillCreate.model_validate(
            {
                "name": "Skill One",
                "description": "Helpful skill",
                "content": "Skill content",
                "source_type": "manual",
                "source_id": None,
                "risk_level": "low",
                "status": "active",
            }
        )
        created_skill = build_skill()

        with patch(
            "app.services.skill_service.ensure_unique_slug",
            return_value="skill-one",
        ), patch(
            "app.services.skill_service.skill_repository.create",
            return_value=created_skill,
        ), patch(
            "app.services.skill_service.serialize_skill",
            return_value=created_skill,
        ), patch(
            "app.services.skill_service.log_service.record_activity"
        ) as mock_activity:
            result = create_skill(self.db, owner_id=self.owner_id, payload=payload)

        self.assertEqual(result, created_skill)
        self.assertEqual(mock_activity.call_args.kwargs["event_type"], "skill.created")
        self.assertEqual(mock_activity.call_args.kwargs["actor_id"], self.owner_id)
        self.assertNotIn("content", str(mock_activity.call_args.kwargs))

    def test_update_skill_writes_activity_and_audit_logs(self):
        existing_skill = build_skill()
        updated_skill = build_skill(name="Skill Two")
        updated_skill.slug = "skill-two"
        payload = SkillUpdate.model_validate({"name": "Skill Two", "risk_level": "medium"})

        with patch(
            "app.services.skill_service.skill_repository.get_by_id",
            return_value=existing_skill,
        ), patch(
            "app.services.skill_service.ensure_unique_slug",
            return_value="skill-two",
        ), patch(
            "app.services.skill_service.skill_repository.update",
            return_value=updated_skill,
        ), patch(
            "app.services.skill_service.serialize_skill",
            return_value=updated_skill,
        ), patch(
            "app.services.skill_service.log_service.record_activity"
        ) as mock_activity, patch(
            "app.services.skill_service.log_service.record_audit"
        ) as mock_audit:
            result = update_skill(self.db, owner_id=self.owner_id, skill_id=existing_skill.id, payload=payload)

        self.assertEqual(result, updated_skill)
        self.assertEqual(mock_activity.call_args.kwargs["event_type"], "skill.updated")
        self.assertEqual(mock_audit.call_args.kwargs["action"], "update")
        self.assertEqual(mock_audit.call_args.kwargs["entity_type"], "skill")
        self.assertEqual(mock_audit.call_args.kwargs["before_data"]["name"], "Skill One")
        self.assertEqual(mock_audit.call_args.kwargs["after_data"]["name"], "Skill Two")

    def test_deactivate_skill_writes_activity_and_audit_logs(self):
        existing_skill = build_skill()
        deactivated_skill = build_skill(status="disabled")
        deactivated_skill.deleted_at = datetime.now(UTC)

        with patch(
            "app.services.skill_service.skill_repository.get_by_id",
            return_value=existing_skill,
        ), patch(
            "app.services.skill_service.skill_repository.soft_delete",
            return_value=deactivated_skill,
        ), patch(
            "app.services.skill_service.serialize_skill",
            return_value=deactivated_skill,
        ), patch(
            "app.services.skill_service.log_service.record_activity"
        ) as mock_activity, patch(
            "app.services.skill_service.log_service.record_audit"
        ) as mock_audit:
            result = deactivate_skill(self.db, owner_id=self.owner_id, skill_id=existing_skill.id)

        self.assertEqual(result, deactivated_skill)
        self.assertEqual(mock_activity.call_args.kwargs["event_type"], "skill.deactivated")
        self.assertEqual(mock_audit.call_args.kwargs["action"], "deactivate")
        self.assertEqual(mock_audit.call_args.kwargs["entity_type"], "skill")


if __name__ == "__main__":
    unittest.main()
