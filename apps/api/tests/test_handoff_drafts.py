import unittest
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.schemas.handoff_draft import HandoffDraftCreateRequest
from app.services.handoff_draft_service import (
    archive_handoff_draft,
    create_handoff_draft,
    get_handoff_draft,
    list_handoff_drafts,
)


def build_agent(*, owner_id: uuid.UUID, name: str, slug: str | None = None):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name=name,
        slug=slug or name.lower().replace(" ", "-"),
        description=f"{name} description",
        role_description=f"{name} role",
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


def build_skill_match(title: str, skill_type: str = "knowledge_skill"):
    return SimpleNamespace(
        skill_id=uuid.uuid4(),
        title=title,
        skill_type=skill_type,
        status="active",
        security_status="safe",
        matched_terms=["task"],
        match_score=12,
        reason=f"Task suggests {skill_type.replace('_', ' ')} work.",
    )


def build_preview_result(*, recommended_agent, candidates, confidence="high"):
    return SimpleNamespace(
        task_text="Summarize the report",
        recommended_agent=recommended_agent,
        candidate_agents=candidates,
        confidence=confidence,
        reasons=["Task overlaps with the agent description."],
        active_skill_matches=list(getattr(recommended_agent, "active_skill_matches", []) or []),
        note="Preview only, no execution.",
    )


def build_candidate(agent, *, score=42, reasons=None, active_skill_matches=None):
    return SimpleNamespace(
        agent_id=agent.id,
        name=agent.name,
        slug=agent.slug,
        description=agent.description,
        role_description=agent.role_description,
        score=score,
        reasons=reasons or [f"{agent.name} matches the task."],
        active_skill_matches=active_skill_matches or [],
    )


def build_draft(
    *,
    owner_id: uuid.UUID,
    selected_agent_id: uuid.UUID,
    recommended_agent_id: uuid.UUID | None,
    status: str = "draft",
):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        task_text="Summarize the report",
        routing_confidence="high",
        routing_reasons=["Task overlaps with the agent description."],
        recommended_agent_id=recommended_agent_id,
        selected_agent_id=selected_agent_id,
        active_skill_matches=[
            {
                "skill_id": str(uuid.uuid4()),
                "title": "Document Summarization",
                "skill_type": "knowledge_skill",
                "match_reason": "Task suggests knowledge skill work.",
            }
        ],
        draft_payload={
            "task_summary": "Summarize the report",
            "handoff_message": "Handoff draft for Research Agent. Task summary: Summarize the report. Matched active skills: Document Summarization. This is a draft only and must not execute.",
            "suggested_steps": [
                "Review the task and confirm the requested outcome.",
                "Use the attached active skills as instruction or capability context only.",
                "Use the matched skills as active guidance: Document Summarization.",
                "Prepare a safe response draft for the user.",
                "Do not execute runtime, tools, workflows, or external calls.",
            ],
            "safety_note": "Draft only, no execution.",
        },
        status=status,
        created_at=now,
        updated_at=now,
    )


class HandoffDraftTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.user_id = uuid.uuid4()
        self.other_user_id = uuid.uuid4()
        self.user = SimpleNamespace(id=self.user_id, role="user")
        self.admin = SimpleNamespace(id=self.user_id, role="admin")

    def test_user_can_create_handoff_draft(self):
        agent = build_agent(owner_id=self.user_id, name="Research Agent")
        match = build_skill_match("Document Summarization")
        candidate = build_candidate(agent, active_skill_matches=[match])
        preview_result = build_preview_result(recommended_agent=candidate, candidates=[candidate])
        draft = build_draft(
            owner_id=self.user_id,
            selected_agent_id=agent.id,
            recommended_agent_id=agent.id,
        )

        with patch(
            "app.services.handoff_draft_service.preview_agent_routing",
            return_value=preview_result,
        ) as mock_preview, patch(
            "app.services.handoff_draft_service.agent_repository.get_by_id",
            return_value=agent,
        ), patch(
            "app.services.handoff_draft_service.handoff_draft_repository.create",
            return_value=draft,
        ) as mock_create:
            result = create_handoff_draft(
                self.db,
                owner_id=self.user_id,
                payload=HandoffDraftCreateRequest(task_text="Summarize the report"),
                current_user=self.user,
            )

        mock_preview.assert_called_once()
        mock_create.assert_called_once()
        self.assertEqual(result.status, "draft")
        self.assertEqual(result.selected_agent.name, "Research Agent")
        self.assertEqual(result.recommended_agent.name, "Research Agent")
        self.assertTrue(result.active_skill_matches)
        self.db.commit.assert_called()

    def test_draft_creation_uses_preview_when_selected_agent_absent(self):
        agent = build_agent(owner_id=self.user_id, name="Research Agent")
        match = build_skill_match("Document Summarization")
        candidate = build_candidate(agent, active_skill_matches=[match])
        preview_result = build_preview_result(recommended_agent=candidate, candidates=[candidate])
        draft = build_draft(
            owner_id=self.user_id,
            selected_agent_id=agent.id,
            recommended_agent_id=agent.id,
        )

        with patch(
            "app.services.handoff_draft_service.preview_agent_routing",
            return_value=preview_result,
        ) as mock_preview, patch(
            "app.services.handoff_draft_service.agent_repository.get_by_id",
            return_value=agent,
        ), patch(
            "app.services.handoff_draft_service.handoff_draft_repository.create",
            return_value=draft,
        ):
            create_handoff_draft(
                self.db,
                owner_id=self.user_id,
                payload=HandoffDraftCreateRequest(task_text="Summarize the report"),
                current_user=self.user,
            )

        mock_preview.assert_called_once()

    def test_user_can_list_own_drafts(self):
        agent = build_agent(owner_id=self.user_id, name="Research Agent")
        draft = build_draft(
            owner_id=self.user_id,
            selected_agent_id=agent.id,
            recommended_agent_id=agent.id,
        )

        with patch(
            "app.services.handoff_draft_service.handoff_draft_repository.list_by_owner",
            return_value=[draft],
        ), patch(
            "app.services.handoff_draft_service.agent_repository.get_by_id",
            return_value=agent,
        ):
            result = list_handoff_drafts(
                self.db,
                owner_id=self.user_id,
                current_user=self.user,
                limit=20,
                offset=0,
            )

        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].selected_agent.name, "Research Agent")
        self.assertEqual(result.items[0].recommended_agent.name, "Research Agent")

    def test_user_can_read_own_draft_detail(self):
        agent = build_agent(owner_id=self.user_id, name="Research Agent")
        draft = build_draft(
            owner_id=self.user_id,
            selected_agent_id=agent.id,
            recommended_agent_id=agent.id,
        )

        with patch(
            "app.services.handoff_draft_service.handoff_draft_repository.get_by_id_for_owner",
            return_value=draft,
        ), patch(
            "app.services.handoff_draft_service.agent_repository.get_by_id",
            return_value=agent,
        ):
            result = get_handoff_draft(
                self.db,
                owner_id=self.user_id,
                draft_id=draft.id,
                current_user=self.user,
            )

        self.assertEqual(result.id, draft.id)
        self.assertEqual(result.draft_payload.safety_note, "Draft only, no execution.")

    def test_user_cannot_access_another_users_draft(self):
        with patch(
            "app.services.handoff_draft_service.handoff_draft_repository.get_by_id_for_owner",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as exc_info:
                get_handoff_draft(
                    self.db,
                    owner_id=self.user_id,
                    draft_id=uuid.uuid4(),
                    current_user=self.user,
                )

        self.assertEqual(exc_info.exception.status_code, 404)

    def test_user_cannot_create_draft_using_other_users_selected_agent(self):
        with patch(
            "app.services.handoff_draft_service.agent_repository.get_by_id",
            return_value=None,
        ) as mock_get_agent, patch(
            "app.services.handoff_draft_service.preview_agent_routing",
        ) as mock_preview:
            with self.assertRaises(HTTPException) as exc_info:
                create_handoff_draft(
                    self.db,
                    owner_id=self.user_id,
                    payload=HandoffDraftCreateRequest(
                        task_text="Summarize the report",
                        selected_agent_id=uuid.uuid4(),
                    ),
                    current_user=self.user,
                )

        self.assertEqual(exc_info.exception.status_code, 404)
        mock_preview.assert_not_called()
        mock_get_agent.assert_called_once()

    def test_response_does_not_expose_other_users_secrets(self):
        agent = build_agent(owner_id=self.user_id, name="Research Agent")
        draft = build_draft(
            owner_id=self.user_id,
            selected_agent_id=agent.id,
            recommended_agent_id=agent.id,
        )

        with patch(
            "app.services.handoff_draft_service.handoff_draft_repository.get_by_id_for_owner",
            return_value=draft,
        ), patch(
            "app.services.handoff_draft_service.agent_repository.get_by_id",
            return_value=agent,
        ):
            result = get_handoff_draft(
                self.db,
                owner_id=self.user_id,
                draft_id=draft.id,
                current_user=self.user,
            )

        self.assertFalse(hasattr(result, "content"))
        self.assertFalse(hasattr(result, "api_key"))
        self.assertFalse(hasattr(result, "token"))
        self.assertFalse(hasattr(result, "password"))
        self.assertFalse(hasattr(result.selected_agent, "content"))

    def test_admin_can_archive_draft(self):
        agent = build_agent(owner_id=self.other_user_id, name="Ops Agent")
        draft = build_draft(
            owner_id=self.other_user_id,
            selected_agent_id=agent.id,
            recommended_agent_id=agent.id,
        )
        draft.status = "draft"
        archived = build_draft(
            owner_id=self.other_user_id,
            selected_agent_id=agent.id,
            recommended_agent_id=agent.id,
            status="archived",
        )
        archived.id = draft.id

        with patch(
            "app.services.handoff_draft_service.handoff_draft_repository.get_by_id",
            return_value=draft,
        ), patch(
            "app.services.handoff_draft_service.handoff_draft_repository.update",
            return_value=archived,
        ), patch(
            "app.services.handoff_draft_service.agent_repository.get_by_id_for_admin",
            return_value=agent,
        ):
            result = archive_handoff_draft(
                self.db,
                owner_id=self.other_user_id,
                draft_id=draft.id,
                current_user=self.admin,
            )

        self.assertEqual(result.status, "archived")


if __name__ == "__main__":
    unittest.main()
