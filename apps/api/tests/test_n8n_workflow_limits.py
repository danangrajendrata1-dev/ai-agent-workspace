import unittest
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.schemas.n8n_workflow import N8nWorkflowCreate, N8nWorkflowUpdate
from app.services.n8n_workflow_service import create_workflow, list_workflows, update_workflow


def build_workflow_payload(name: str = "Email Draft", status: str = "active") -> N8nWorkflowCreate:
    return N8nWorkflowCreate(
        name=name,
        slug=None,
        description="Draft workflow metadata",
        workflow_external_id=None,
        trigger_type="manual",
        webhook_url_reference=None,
        status=status,
        risk_level="low",
        approval_required=False,
        metadata={"source": "dashboard"},
    )


def build_workflow(owner_id: uuid.UUID, *, name: str, slug: str, status: str = "inactive") -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name=name,
        slug=slug,
        description="Draft workflow metadata",
        workflow_external_id=None,
        trigger_type="manual",
        webhook_url_reference=None,
        status=status,
        risk_level="low",
        approval_required=False,
        metadata_json={"source": "dashboard"},
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


class N8nWorkflowLimitsTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.owner_id = uuid.uuid4()

    def test_free_user_cannot_access_workflows(self):
        user = SimpleNamespace(
            id=self.owner_id,
            role="user",
            subscription_plan="free",
            is_active=True,
            deleted_at=None,
        )

        with patch("app.services.n8n_workflow_service.user_repository.get_by_id", return_value=user), patch(
            "app.services.n8n_workflow_service.n8n_workflow_repository.list_by_owner"
        ) as mock_list:
            with self.assertRaises(HTTPException) as exc_info:
                list_workflows(self.db, owner_id=self.owner_id)

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertIn("does not include n8n access", exc_info.exception.detail)
        mock_list.assert_not_called()

    def test_free_user_cannot_save_workflow(self):
        user = SimpleNamespace(
            id=self.owner_id,
            role="user",
            subscription_plan="free",
            is_active=True,
            deleted_at=None,
        )

        with patch("app.services.n8n_workflow_service.user_repository.get_by_id", return_value=user), patch(
            "app.services.n8n_workflow_service.n8n_workflow_repository.count_saved_by_owner"
        ) as mock_count, patch("app.services.n8n_workflow_service.n8n_workflow_repository.create") as mock_create:
            with self.assertRaises(HTTPException) as exc_info:
                create_workflow(self.db, owner_id=self.owner_id, payload=build_workflow_payload())

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertIn("does not include n8n access", exc_info.exception.detail)
        mock_count.assert_not_called()
        mock_create.assert_not_called()

    def test_pro_user_can_save_one_workflow(self):
        user = SimpleNamespace(
            id=self.owner_id,
            role="user",
            subscription_plan="pro",
            is_active=True,
            deleted_at=None,
        )
        workflow = build_workflow(self.owner_id, name="Workflow 1", slug="workflow-1")

        with patch("app.services.n8n_workflow_service.user_repository.get_by_id", return_value=user), patch(
            "app.services.n8n_workflow_service.validate_no_plaintext_secret"
        ), patch("app.services.n8n_workflow_service.ensure_unique_slug", return_value="workflow-1"), patch(
            "app.services.n8n_workflow_service.n8n_workflow_repository.count_saved_by_owner",
            return_value=0,
        ), patch("app.services.n8n_workflow_service.n8n_workflow_repository.create", return_value=workflow) as mock_create, patch(
            "app.services.n8n_workflow_service.log_service.record_activity"
        ), patch(
            "app.services.n8n_workflow_service.serialize_workflow",
            return_value=workflow,
        ):
            result = create_workflow(self.db, owner_id=self.owner_id, payload=build_workflow_payload())

        self.assertEqual(result, workflow)
        created_payload = mock_create.call_args.args[1]
        self.assertEqual(created_payload["status"], "inactive")
        mock_create.assert_called_once()

    def test_pro_user_cannot_save_second_workflow(self):
        user = SimpleNamespace(
            id=self.owner_id,
            role="user",
            subscription_plan="pro",
            is_active=True,
            deleted_at=None,
        )

        with patch("app.services.n8n_workflow_service.user_repository.get_by_id", return_value=user), patch(
            "app.services.n8n_workflow_service.n8n_workflow_repository.count_saved_by_owner",
            return_value=1,
        ), patch("app.services.n8n_workflow_service.n8n_workflow_repository.create") as mock_create:
            with self.assertRaises(HTTPException) as exc_info:
                create_workflow(self.db, owner_id=self.owner_id, payload=build_workflow_payload("Workflow 2"))

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertIn("Your Pro plan allows 1 saved workflow", exc_info.exception.detail)
        mock_create.assert_not_called()

    def test_executive_user_can_save_up_to_ten_workflows(self):
        user = SimpleNamespace(
            id=self.owner_id,
            role="user",
            subscription_plan="executive",
            is_active=True,
            deleted_at=None,
        )
        workflow = build_workflow(self.owner_id, name="Executive Workflow", slug="executive-workflow")

        with patch("app.services.n8n_workflow_service.user_repository.get_by_id", return_value=user), patch(
            "app.services.n8n_workflow_service.validate_no_plaintext_secret"
        ), patch("app.services.n8n_workflow_service.ensure_unique_slug", return_value="executive-workflow"), patch(
            "app.services.n8n_workflow_service.n8n_workflow_repository.count_saved_by_owner",
            return_value=9,
        ), patch("app.services.n8n_workflow_service.n8n_workflow_repository.create", return_value=workflow) as mock_create, patch(
            "app.services.n8n_workflow_service.log_service.record_activity"
        ), patch(
            "app.services.n8n_workflow_service.serialize_workflow",
            return_value=workflow,
        ):
            result = create_workflow(self.db, owner_id=self.owner_id, payload=build_workflow_payload("Executive Workflow"))

        self.assertEqual(result, workflow)
        mock_create.assert_called_once()

        with patch("app.services.n8n_workflow_service.user_repository.get_by_id", return_value=user), patch(
            "app.services.n8n_workflow_service.n8n_workflow_repository.count_saved_by_owner",
            return_value=10,
        ), patch("app.services.n8n_workflow_service.n8n_workflow_repository.create") as blocked_create:
            with self.assertRaises(HTTPException) as exc_info:
                create_workflow(self.db, owner_id=self.owner_id, payload=build_workflow_payload("Executive Workflow 2"))

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertIn("Your Executive plan allows up to 10 saved workflows", exc_info.exception.detail)
        blocked_create.assert_not_called()

    def test_admin_bypasses_workflow_limit(self):
        user = SimpleNamespace(
            id=self.owner_id,
            role="admin",
            subscription_plan="free",
            is_active=True,
            deleted_at=None,
        )
        workflow = build_workflow(self.owner_id, name="Admin Workflow", slug="admin-workflow")

        with patch("app.services.n8n_workflow_service.user_repository.get_by_id", return_value=user), patch(
            "app.services.n8n_workflow_service.validate_no_plaintext_secret"
        ), patch("app.services.n8n_workflow_service.ensure_unique_slug", return_value="admin-workflow"), patch(
            "app.services.n8n_workflow_service.n8n_workflow_repository.count_saved_by_owner"
        ) as mock_count, patch("app.services.n8n_workflow_service.n8n_workflow_repository.create", return_value=workflow) as mock_create, patch(
            "app.services.n8n_workflow_service.log_service.record_activity"
        ), patch(
            "app.services.n8n_workflow_service.serialize_workflow",
            return_value=workflow,
        ):
            result = create_workflow(self.db, owner_id=self.owner_id, payload=build_workflow_payload("Admin Workflow"))

        self.assertEqual(result, workflow)
        mock_count.assert_not_called()
        mock_create.assert_called_once()

    def test_workflow_status_is_coerced_to_inactive_on_update(self):
        user = SimpleNamespace(
            id=self.owner_id,
            role="user",
            subscription_plan="pro",
            is_active=True,
            deleted_at=None,
        )
        current_workflow = build_workflow(self.owner_id, name="Workflow", slug="workflow", status="active")
        updated_workflow = build_workflow(self.owner_id, name="Workflow", slug="workflow", status="inactive")
        update_payload = N8nWorkflowUpdate(
            name="Workflow",
            slug=None,
            description="Draft workflow metadata",
            workflow_external_id=None,
            trigger_type="manual",
            webhook_url_reference=None,
            status="active",
            risk_level="low",
            approval_required=False,
            metadata={"source": "dashboard"},
        )

        with patch("app.services.n8n_workflow_service.user_repository.get_by_id", return_value=user), patch(
            "app.services.n8n_workflow_service.n8n_workflow_repository.get_by_id",
            return_value=current_workflow,
        ), patch("app.services.n8n_workflow_service.validate_no_plaintext_secret"), patch(
            "app.services.n8n_workflow_service.ensure_unique_slug",
            return_value="workflow",
        ), patch("app.services.n8n_workflow_service.n8n_workflow_repository.update", return_value=updated_workflow) as mock_update, patch(
            "app.services.n8n_workflow_service.log_service.record_activity"
        ), patch(
            "app.services.n8n_workflow_service.serialize_workflow",
            return_value=updated_workflow,
        ):
            result = update_workflow(
                self.db,
                owner_id=self.owner_id,
                workflow_id=current_workflow.id,
                payload=update_payload,
            )

        self.assertEqual(result, updated_workflow)
        candidate = mock_update.call_args.args[2]
        self.assertEqual(candidate["status"], "inactive")


if __name__ == "__main__":
    unittest.main()
