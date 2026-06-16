import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from app.core.security import create_access_token
from app.schemas.agent import TaskDraftResponse
from app.services.agent_task_draft_service import create_agent_task_draft


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


def auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


def build_task_draft_response(*, task_text: str, selected_agent_id: str, selected_agent_name: str) -> TaskDraftResponse:
    return TaskDraftResponse(
        task_text=task_text,
        selected_agent_id=selected_agent_id,
        selected_agent_name=selected_agent_name,
        confidence="high",
        reasons=["Task mentions document summarization."],
        relevant_skills=[
            {
                "skill_id": str(uuid.uuid4()),
                "title": "Document Summarization",
                "skill_type": "knowledge_skill",
                "relevance_note": "Task matches the skill title.",
            }
        ],
        task_summary="Please summarize these notes for the workspace.",
        safety_note="This is a draft preview only. No agent has been run. No skill has been executed.",
        status="draft_only",
        candidate_agents=[
            {
                "agent_id": selected_agent_id,
                "name": selected_agent_name,
                "slug": "document-summarization",
                "description": "Summarize notes and docs.",
                "role_description": "Workspace summarizer.",
                "score": 68,
                "reasons": ["Task mentions document summarization."],
                "active_skill_matches": [],
            }
        ],
    )


def test_task_draft_route_requires_authentication(client):
    response = client.post("/agents/task-draft", json={"task_text": "Summarize these notes."})

    assert response.status_code == 401


def test_task_text_empty_is_rejected(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_task_draft_service.create_agent_task_draft"
    ) as mock_create:
        response = client.post("/agents/task-draft", headers=headers, json={"task_text": ""})

    assert response.status_code == 422
    mock_create.assert_not_called()


def test_task_text_whitespace_only_is_rejected(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_task_draft_service.create_agent_task_draft"
    ) as mock_create:
        response = client.post("/agents/task-draft", headers=headers, json={"task_text": "   "})

    assert response.status_code == 422
    mock_create.assert_not_called()


def test_route_returns_valid_task_draft_response(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    response_model = build_task_draft_response(
        task_text="Please summarize these notes for the workspace.",
        selected_agent_id=str(uuid.uuid4()),
        selected_agent_name="Document Summarization",
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_task_draft_service.create_agent_task_draft",
        return_value=response_model,
    ) as mock_create:
        response = client.post("/agents/task-draft", headers=headers, json={"task_text": "Please summarize these notes for the workspace."})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "draft_only"
    assert payload["safety_note"] == "This is a draft preview only. No agent has been run. No skill has been executed."
    assert payload["selected_agent_name"] == "Document Summarization"
    assert payload["confidence"] == "high"
    mock_create.assert_called_once()


def test_service_generates_draft_from_own_active_skills():
    db = SimpleNamespace()
    user_id = uuid.uuid4()
    own_agent = build_agent(
        owner_id=user_id,
        name="Document Summarization",
        description="Summarize reports and notes.",
        role_description="Helpful document summarization agent.",
    )
    other_agent = build_agent(
        owner_id=uuid.uuid4(),
        name="Ops Helper",
        description="Operations helper.",
        role_description="Operations support agent.",
    )
    own_skill = build_active_skill(title="Document Summarization", skill_type="knowledge_skill")
    other_skill = build_active_skill(title="Workflow Ops", skill_type="workflow_skill")

    def list_active_skills_side_effect(*args, **kwargs):
        agent_id = kwargs["agent_id"]
        if agent_id == own_agent.id:
            return [own_skill]
        if agent_id == other_agent.id:
            return [other_skill]
        return []

    with patch(
        "app.services.agent_routing_service.agent_repository.list_by_owner",
        return_value=[own_agent],
    ) as mock_list_by_owner, patch(
        "app.services.agent_routing_service.agent_repository.list_all_active",
        return_value=[own_agent, other_agent],
    ) as mock_list_all, patch(
        "app.services.agent_routing_service.skill_service.list_active_agent_skills",
        side_effect=list_active_skills_side_effect,
    ):
        result = create_agent_task_draft(
            db,
            current_user=SimpleNamespace(id=user_id, role="user"),
            task_text="Please do document summarization for these notes.",
        )

    assert result.status == "draft_only"
    assert result.safety_note == "This is a draft preview only. No agent has been run. No skill has been executed."
    assert result.selected_agent_name == "Document Summarization"
    assert result.selected_agent_id == str(own_agent.id)
    assert result.confidence in {"high", "medium", "low"}
    assert result.task_summary == "Please do document summarization for these notes."
    assert len(result.candidate_agents) == 1
    assert result.candidate_agents[0]["name"] == "Document Summarization"
    assert len(result.relevant_skills) == 1
    assert result.relevant_skills[0].title == "Document Summarization"
    assert result.relevant_skills[0].skill_type == "knowledge_skill"
    mock_list_by_owner.assert_called_once()
    mock_list_all.assert_not_called()


def test_service_admin_can_draft_across_all_agents():
    db = SimpleNamespace()
    user_id = uuid.uuid4()
    other_owner_id = uuid.uuid4()
    admin_agent = build_agent(
        owner_id=other_owner_id,
        name="Research Assistant",
        description="Research and summary helper.",
        role_description="Research support agent.",
    )
    own_agent = build_agent(
        owner_id=user_id,
        name="Workflow Ops",
        description="Workflow automation helper.",
        role_description="Operations and automation agent.",
    )
    admin_skill = build_active_skill(title="Research Assistant", skill_type="knowledge_skill")
    own_skill = build_active_skill(title="Workflow Ops", skill_type="workflow_skill")

    def list_active_skills_side_effect(*args, **kwargs):
        agent_id = kwargs["agent_id"]
        if agent_id == admin_agent.id:
            return [admin_skill]
        if agent_id == own_agent.id:
            return [own_skill]
        return []

    with patch(
        "app.services.agent_routing_service.agent_repository.list_all_active",
        return_value=[admin_agent, own_agent],
    ) as mock_list_all, patch(
        "app.services.agent_routing_service.skill_service.list_active_agent_skills",
        side_effect=list_active_skills_side_effect,
    ):
        result = create_agent_task_draft(
            db,
            current_user=SimpleNamespace(id=user_id, role="admin"),
            task_text="Research Assistant, summarize these findings.",
        )

    assert result.status == "draft_only"
    assert result.safety_note == "This is a draft preview only. No agent has been run. No skill has been executed."
    assert result.selected_agent_name == "Research Assistant"
    assert result.selected_agent_id == str(admin_agent.id)
    assert result.confidence in {"high", "medium", "low"}
    assert any(candidate["name"] == "Research Assistant" for candidate in result.candidate_agents)
    assert len(result.relevant_skills) == 1
    assert result.relevant_skills[0].title == "Research Assistant"
    mock_list_all.assert_called_once()
