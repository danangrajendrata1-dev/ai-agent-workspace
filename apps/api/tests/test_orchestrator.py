import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.core.security import create_access_token
from app.schemas.agent_chat import AgentChatRequest
from app.services.orchestrator_service import clear_orchestrator_rate_limiter, orchestrate_workspace_chat


def auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    clear_orchestrator_rate_limiter()
    yield
    clear_orchestrator_rate_limiter()


@pytest.fixture(autouse=True)
def mute_orchestrator_activity_log():
    with patch("app.services.orchestrator_service.log_service.record_activity", return_value=None):
        yield


def build_agent(*, owner_id: uuid.UUID, name: str = "Workspace Agent"):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name=name,
        slug=name.lower().replace(" ", "-"),
        description="Workspace helper agent.",
        role_description="Helpful workspace assistant.",
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


def build_skill_assignment(*, title: str, skill_type: str = "prompt_skill"):
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
    )
    return SimpleNamespace(
        id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        skill_id=skill_id,
        is_enabled=True,
        created_at=now,
        skill=skill,
    )


def build_preview_candidate(agent, *, confidence: str = "high", reasons: list[str] | None = None):
    return SimpleNamespace(
        agent_id=agent.id,
        name=agent.name,
        slug=agent.slug,
        description=agent.description,
        role_description=agent.role_description,
        score=99,
        reasons=reasons or ["Matched workspace task."],
        active_skill_matches=[],
        confidence=confidence,
    )


def build_preview_result(*, recommended_agent, confidence: str, reasons: list[str] | None = None):
    return SimpleNamespace(
        task_text="Example task",
        recommended_agent=recommended_agent,
        candidate_agents=[recommended_agent] if recommended_agent is not None else [],
        confidence=confidence,
        reasons=reasons or ["Matched workspace task."],
        active_skill_matches=[],
        note="Preview only, no execution.",
    )


def build_db():
    return SimpleNamespace(commit=lambda: None)


def test_orchestrator_route_requires_authentication(client):
    response = client.post(
        "/orchestrator/chat",
        json={"task_text": "Summarize the report", "messages": []},
    )

    assert response.status_code == 401


def test_orchestrator_rejects_empty_task_text(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user):
        response = client.post(
            "/orchestrator/chat",
            headers=headers,
            json={"task_text": "", "messages": []},
        )

    assert response.status_code == 422


def test_orchestrator_rejects_whitespace_only_task_text(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user):
        response = client.post(
            "/orchestrator/chat",
            headers=headers,
            json={"task_text": "   ", "messages": []},
        )

    assert response.status_code == 422


def test_orchestrator_rejects_too_many_messages(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    messages = [{"role": "user", "content": f"Message {index + 1}"} for index in range(51)]

    with patch("app.services.auth_service.get_current_active_user", return_value=user):
        response = client.post(
            "/orchestrator/chat",
            headers=headers,
            json={"task_text": "Summarize the report", "messages": messages},
        )

    assert response.status_code == 422


def test_orchestrator_fallback_when_user_has_no_agents(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_routing_service.agent_repository.list_by_owner",
        return_value=[],
    ), patch(
        "app.services.agent_routing_service.skill_service.list_active_agent_skills",
        return_value=[],
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent"
    ) as mock_chat:
        response = client.post(
            "/orchestrator/chat",
            headers=headers,
            json={"task_text": "Summarize the report", "messages": []},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "fallback"
    assert payload["confidence"] == "none"
    assert payload["reply"].startswith("Maaf, saya tidak menemukan agent yang sesuai")
    assert payload["routed_to_agent_id"] is None
    assert payload["provider"] is None
    assert payload["model"] is None
    mock_chat.assert_not_called()


def test_orchestrator_fallback_when_confidence_low_does_not_call_agent_chat(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    agent = build_agent(owner_id=user.id)
    preview_result = build_preview_result(
        recommended_agent=None,
        confidence="low",
        reasons=["No strong keyword overlap found."],
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.orchestrator_service.agent_routing_service.preview_agent_routing",
        return_value=preview_result,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent"
    ) as mock_chat:
        response = client.post(
            "/orchestrator/chat",
            headers=headers,
            json={"task_text": "Plan a surprise party", "messages": []},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "fallback"
    assert payload["confidence"] == "none"
    assert payload["routing_reasons"] == ["No strong keyword overlap found."]
    assert payload["routed_to_agent_id"] is None
    mock_chat.assert_not_called()


def test_orchestrator_routes_when_confidence_medium(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    agent = build_agent(owner_id=user.id, name="Document Summarizer")
    preview_result = build_preview_result(
        recommended_agent=build_preview_candidate(agent, confidence="medium"),
        confidence="medium",
        reasons=["Task overlaps with document summarization work."],
    )
    captured = {}

    def fake_chat_with_agent(*args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            agent_id=agent.id,
            agent_name=agent.name,
            reply="Agent reply",
            provider="openai",
            model="gpt-4o-mini",
            prompt_skills_used=["Prompt Skill"],
            knowledge_skills_used=["Knowledge Skill"],
            knowledge_truncated=False,
            warning=None,
        )

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.orchestrator_service.agent_routing_service.preview_agent_routing",
        return_value=preview_result,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent",
        side_effect=fake_chat_with_agent,
    ):
        response = client.post(
            "/orchestrator/chat",
            headers=headers,
            json={"task_text": "Please summarize this document", "messages": []},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "routed"
    assert payload["confidence"] == "medium"
    assert payload["routed_to_agent_id"] == str(agent.id)
    assert payload["routed_to_agent_name"] == "Document Summarizer"
    assert payload["reply"] == "Agent reply"
    assert payload["provider"] == "openai"
    assert payload["model"] == "gpt-4o-mini"
    assert payload["prompt_skills_used"] == ["Prompt Skill"]
    assert payload["knowledge_skills_used"] == ["Knowledge Skill"]
    assert payload["knowledge_truncated"] is False
    assert captured["payload"].messages[0].content == "Please summarize this document"


def test_orchestrator_routes_when_confidence_high_and_preserves_messages(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    agent = build_agent(owner_id=user.id, name="Research Agent")
    preview_result = build_preview_result(
        recommended_agent=build_preview_candidate(agent, confidence="high"),
        confidence="high",
        reasons=["Task mentions research work."],
    )
    captured = {}
    request_messages = [
        {"role": "user", "content": "Prepare the report"},
        {"role": "assistant", "content": "I will help."},
    ]

    def fake_chat_with_agent(*args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            agent_id=agent.id,
            agent_name=agent.name,
            reply="Research reply",
            provider="anthropic",
            model="claude-3-5-sonnet",
            prompt_skills_used=["Research Prompt"],
            knowledge_skills_used=["Research Knowledge"],
            knowledge_truncated=True,
            warning="Knowledge context truncated due to length limit",
        )

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.orchestrator_service.agent_routing_service.preview_agent_routing",
        return_value=preview_result,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent",
        side_effect=fake_chat_with_agent,
    ):
        response = client.post(
            "/orchestrator/chat",
            headers=headers,
            json={"task_text": "Please handle the research task", "messages": request_messages},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "routed"
    assert payload["confidence"] == "high"
    assert payload["routed_to_agent_id"] == str(agent.id)
    assert payload["reply"] == "Research reply"
    assert payload["provider"] == "anthropic"
    assert payload["model"] == "claude-3-5-sonnet"
    assert payload["prompt_skills_used"] == ["Research Prompt"]
    assert payload["knowledge_skills_used"] == ["Research Knowledge"]
    assert payload["knowledge_truncated"] is True
    assert payload["warning"] == "Knowledge context truncated due to length limit"
    assert captured["payload"].messages[0].content == "Prepare the report"
    assert captured["payload"].messages[1].content == "I will help."


def test_orchestrator_user_cannot_route_against_other_users_agent(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    other_user_id = uuid.uuid4()
    headers = auth_headers(user.id)
    own_agent = build_agent(owner_id=user.id, name="Own Agent")
    other_agent = build_agent(owner_id=other_user_id, name="Other Agent")
    own_skill = build_skill_assignment(title="Own Agent", skill_type="prompt_skill")

    def list_active_skills_side_effect(*args, **kwargs):
        agent_id = kwargs["agent_id"]
        if agent_id == own_agent.id:
            return [own_skill]
        if agent_id == other_agent.id:
            return []
        return []

    def fake_chat_with_agent(*args, **kwargs):
        return SimpleNamespace(
            agent_id=own_agent.id,
            agent_name=own_agent.name,
            reply="Own agent reply",
            provider="openai",
            model="gpt-4o-mini",
            prompt_skills_used=["Own Agent"],
            knowledge_skills_used=[],
            knowledge_truncated=False,
            warning=None,
        )

    with patch(
        "app.services.agent_routing_service.agent_repository.list_by_owner",
        return_value=[own_agent],
    ), patch(
        "app.services.agent_routing_service.skill_service.list_active_agent_skills",
        side_effect=list_active_skills_side_effect,
    ), patch(
        "app.services.auth_service.get_current_active_user",
        return_value=user,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent",
        side_effect=fake_chat_with_agent,
    ):
        response = client.post(
            "/orchestrator/chat",
            headers=headers,
            json={"task_text": "Own Agent please help", "messages": []},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "routed"
    assert payload["routed_to_agent_id"] == str(own_agent.id)
    assert payload["routed_to_agent_name"] == "Own Agent"


def test_orchestrator_admin_can_route_across_all_agents(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="admin")
    headers = auth_headers(user.id)
    admin_agent = build_agent(owner_id=uuid.uuid4(), name="Admin Research")
    second_agent = build_agent(owner_id=uuid.uuid4(), name="Workflow Ops")
    admin_skill = build_skill_assignment(title="Admin Research", skill_type="prompt_skill")

    def list_active_skills_side_effect(*args, **kwargs):
        agent_id = kwargs["agent_id"]
        if agent_id == admin_agent.id:
            return [admin_skill]
        if agent_id == second_agent.id:
            return []
        return []

    def fake_chat_with_agent(*args, **kwargs):
        return SimpleNamespace(
            agent_id=admin_agent.id,
            agent_name=admin_agent.name,
            reply="Admin reply",
            provider="openrouter",
            model="openrouter-model",
            prompt_skills_used=["Admin Research"],
            knowledge_skills_used=[],
            knowledge_truncated=False,
            warning=None,
        )

    with patch(
        "app.services.agent_routing_service.agent_repository.list_all_active",
        return_value=[admin_agent, second_agent],
    ), patch(
        "app.services.agent_routing_service.skill_service.list_active_agent_skills",
        side_effect=list_active_skills_side_effect,
    ), patch(
        "app.services.auth_service.get_current_active_user",
        return_value=user,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent",
        side_effect=fake_chat_with_agent,
    ):
        response = client.post(
            "/orchestrator/chat",
            headers=headers,
            json={"task_text": "Admin Research please", "messages": []},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "routed"
    assert payload["routed_to_agent_id"] == str(admin_agent.id)
    assert payload["routed_to_agent_name"] == "Admin Research"
    assert payload["provider"] == "openrouter"


def test_orchestrator_routed_error_returns_safe_reply(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    agent = build_agent(owner_id=user.id, name="Research Agent")
    preview_result = build_preview_result(
        recommended_agent=build_preview_candidate(agent, confidence="high"),
        confidence="high",
        reasons=["Task mentions research work."],
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.orchestrator_service.agent_routing_service.preview_agent_routing",
        return_value=preview_result,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent",
        side_effect=HTTPException(
            status_code=400,
            detail="No API key found. Please configure your provider first.",
        ),
    ):
        response = client.post(
            "/orchestrator/chat",
            headers=headers,
            json={"task_text": "Research the document", "messages": []},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "routed"
    assert payload["reply"] == "No API key found. Please configure your provider first."
    assert payload["warning"] == "No API key found. Please configure your provider first."
    assert payload["provider"] is None
    assert payload["model"] is None
    assert "encrypted-secret-value" not in response.text
    assert "raw_response" not in response.text


def test_orchestrator_route_rate_limit_blocks_21st_request(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    agent = build_agent(owner_id=user.id)
    preview_result = build_preview_result(
        recommended_agent=build_preview_candidate(agent, confidence="high"),
        confidence="high",
        reasons=["Matched workspace task."],
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.orchestrator_service.agent_routing_service.preview_agent_routing",
        return_value=preview_result,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent",
        return_value=SimpleNamespace(
            agent_id=agent.id,
            agent_name=agent.name,
            reply="Agent reply",
            provider="openai",
            model="gpt-4o-mini",
            prompt_skills_used=[],
            knowledge_skills_used=[],
            knowledge_truncated=False,
            warning=None,
        ),
    ):
        statuses = []
        for _ in range(21):
            response = client.post(
                "/orchestrator/chat",
                headers=headers,
                json={"task_text": "Summarize the report", "messages": []},
            )
            statuses.append(response.status_code)

    assert statuses[:20] == [200] * 20
    assert statuses[20] == 429
