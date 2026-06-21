import json
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from app.core.database import SessionLocal
from app.core.provider_api_keys import encrypt_api_key
from app.core.security import create_access_token
from app.models.chat_session import ChatSession
from app.repositories import (
    agent_repository,
    model_provider_api_key_repository,
    model_provider_setting_repository,
    session_repository,
    user_repository,
)
from app.schemas.agent_chat import AgentChatRequest
from app.schemas.orchestrator import OrchestratorRequest
from app.services import session_service


def auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


def build_user(
    db,
    *,
    role: str = "user",
    subscription_plan: str = "pro",
    email_prefix: str = "session-user",
):
    user = user_repository.create_user(
        db,
        email=f"{email_prefix}-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hash",
        display_name="Session User",
        role=role,
        subscription_plan=subscription_plan,
    )
    db.commit()
    db.refresh(user)
    return SimpleNamespace(
        id=user.id,
        role=user.role,
        subscription_plan=user.subscription_plan,
        email=user.email,
        display_name=user.display_name,
    )


def build_agent(db, *, owner_id: uuid.UUID, name: str):
    agent = agent_repository.create(
        db,
        {
            "owner_id": owner_id,
            "name": name,
            "slug": f"{name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}",
            "description": f"{name} description.",
            "role_description": f"{name} role instruction.",
            "default_model_provider_id": None,
            "default_model_name": "gpt-4o-mini",
            "status": "active",
            "max_steps": 10,
            "max_runtime_seconds": 300,
            "max_token_budget": None,
            "requires_approval_by_default": False,
        },
    )
    db.commit()
    db.refresh(agent)
    return SimpleNamespace(
        id=agent.id,
        owner_id=agent.owner_id,
        name=agent.name,
        slug=agent.slug,
    )


def build_provider_config(db, *, owner_id: uuid.UUID, provider: str = "openai", model: str = "gpt-4o-mini"):
    setting = model_provider_setting_repository.create_default(db, owner_id)
    setting.preferred_provider = provider
    setting.preferred_model = model
    db.add(setting)
    db.commit()
    db.refresh(setting)

    api_key = "sk-test-12345678"
    record = model_provider_api_key_repository.create(
        db,
        owner_id=owner_id,
        provider=provider,
        encrypted_api_key=encrypt_api_key(api_key),
        key_last4=api_key[-4:],
        key_prefix_masked="********",
        connection_status="connected",
    )
    return setting, record


def build_session_messages(title: str, assistant_reply: str):
    return [{"role": "user", "content": title}], assistant_reply


def test_sessions_route_requires_authentication(client):
    response = client.get("/sessions")

    assert response.status_code == 401


def test_session_routes_list_detail_delete_are_owner_only(client):
    with SessionLocal() as db:
        owner = build_user(db, email_prefix="owner")
        other = build_user(db, email_prefix="other")
        session_a = session_service.upsert_chat_session(
            db,
            user_id=owner.id,
            session_type=session_service.SESSION_TYPE_ORCHESTRATOR,
            messages=[{"role": "user", "content": "First session"}],
            assistant_reply="Assistant reply one",
        )
        session_b = session_service.upsert_chat_session(
            db,
            user_id=owner.id,
            session_type=session_service.SESSION_TYPE_ORCHESTRATOR,
            messages=[{"role": "user", "content": "Second session"}],
            assistant_reply="Assistant reply two",
        )
        session_service.upsert_chat_session(
            db,
            user_id=other.id,
            session_type=session_service.SESSION_TYPE_ORCHESTRATOR,
            messages=[{"role": "user", "content": "Other user session"}],
            assistant_reply="Other reply",
        )

    owner_user = SimpleNamespace(id=owner.id, role=owner.role)
    other_user = SimpleNamespace(id=other.id, role=other.role)

    with patch("app.services.auth_service.get_current_active_user", return_value=owner_user):
        response = client.get("/sessions", headers=auth_headers(owner.id))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["sessions"]) == 2
    assert payload["sessions"][0]["message_count"] >= 2
    assert "messages_encrypted" not in payload["sessions"][0]

    with SessionLocal() as db:
        raw_session = db.get(ChatSession, session_a.id)
        assert raw_session is not None
        plaintext = json.dumps(
            [
                {"role": "user", "content": "First session"},
                {"role": "assistant", "content": "Assistant reply one"},
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        assert raw_session.messages_encrypted != plaintext
        assert "First session" not in raw_session.messages_encrypted

    with patch("app.services.auth_service.get_current_active_user", return_value=owner_user):
        response = client.get(f"/sessions/{session_a.id}", headers=auth_headers(owner.id))

    assert response.status_code == 200
    detail = response.json()
    assert detail["title"] == "First session"
    assert detail["messages"][0]["content"] == "First session"
    assert detail["messages"][1]["content"] == "Assistant reply one"
    assert "messages_encrypted" not in detail

    with patch("app.services.auth_service.get_current_active_user", return_value=other_user):
        response = client.get(f"/sessions/{session_a.id}", headers=auth_headers(other.id))

    assert response.status_code == 404

    with patch("app.services.auth_service.get_current_active_user", return_value=other_user):
        response = client.delete(f"/sessions/{session_a.id}", headers=auth_headers(other.id))

    assert response.status_code == 404

    with patch("app.services.auth_service.get_current_active_user", return_value=owner_user):
        response = client.delete(f"/sessions/{session_a.id}", headers=auth_headers(owner.id))

    assert response.status_code == 200
    assert response.json() == {"success": True}

    with SessionLocal() as db:
        assert session_repository.get_session(db, session_a.id, owner.id) is None


def test_agent_chat_creates_updates_and_persists_session(client):
    with SessionLocal() as db:
        owner = build_user(db, email_prefix="agent-owner")
        agent = build_agent(db, owner_id=owner.id, name="Session Agent")
        build_provider_config(db, owner_id=owner.id)

    current_user = SimpleNamespace(id=owner.id, role=owner.role)
    headers = auth_headers(owner.id)
    provider_results = [
        {"reply": "Agent reply one", "prompt_tokens": 11, "completion_tokens": 7},
        {"reply": "Agent reply two", "prompt_tokens": 13, "completion_tokens": 8},
    ]

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.agent_chat_service.call_provider_chat_completion",
        side_effect=provider_results,
    ), patch(
        "app.services.agent_chat_service.log_service.record_activity",
        return_value=None,
    ):
        response = client.post(
            f"/agents/{agent.id}/chat",
            headers=headers,
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )

    assert response.status_code == 200
    first_payload = response.json()
    assert first_payload["session_id"] is not None
    session_id = first_payload["session_id"]

    with SessionLocal() as db:
        raw_session = db.get(ChatSession, uuid.UUID(session_id))
        assert raw_session is not None
        assert "Hello" not in raw_session.messages_encrypted

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user):
        response = client.get(f"/sessions/{session_id}", headers=headers)

    assert response.status_code == 200
    detail = response.json()
    assert detail["messages"][0]["content"] == "Hello"
    assert detail["messages"][1]["content"] == "Agent reply one"

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.agent_chat_service.call_provider_chat_completion",
        side_effect=provider_results[1:],
    ), patch(
        "app.services.agent_chat_service.log_service.record_activity",
        return_value=None,
    ):
        response = client.post(
            f"/agents/{agent.id}/chat",
            headers=headers,
            json={
                "session_id": session_id,
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Agent reply one"},
                    {"role": "user", "content": "Continue"},
                ],
            },
        )

    assert response.status_code == 200
    assert response.json()["session_id"] == session_id

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user):
        response = client.get(f"/sessions/{session_id}", headers=headers)

    assert response.status_code == 200
    detail = response.json()
    assert len(detail["messages"]) == 4
    assert detail["messages"][-1]["content"] == "Agent reply two"


def test_agent_chat_rejects_session_agent_mismatch(client):
    with SessionLocal() as db:
        owner = build_user(db, email_prefix="mismatch-owner")
        agent_one = build_agent(db, owner_id=owner.id, name="Agent One")
        agent_two = build_agent(db, owner_id=owner.id, name="Agent Two")
        build_provider_config(db, owner_id=owner.id)
        session_record = session_service.upsert_chat_session(
            db,
            user_id=owner.id,
            session_type=session_service.SESSION_TYPE_AGENT,
            agent_id=agent_one.id,
            messages=[{"role": "user", "content": "Hello"}],
            assistant_reply="Agent One reply",
        )

    current_user = SimpleNamespace(id=owner.id, role=owner.role)
    headers = auth_headers(owner.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.agent_chat_service.call_provider_chat_completion"
    ) as mock_provider:
        response = client.post(
            f"/agents/{agent_two.id}/chat",
            headers=headers,
            json={
                "session_id": str(session_record.id),
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Agent One reply"},
                    {"role": "user", "content": "Mismatch"},
                ],
            },
        )

    assert response.status_code == 400
    mock_provider.assert_not_called()


def test_agent_chat_rejects_other_users_session(client):
    with SessionLocal() as db:
        owner_one = build_user(db, email_prefix="session-owner")
        owner_two = build_user(db, email_prefix="session-other")
        agent_one = build_agent(db, owner_id=owner_one.id, name="Owner One Agent")
        agent_two = build_agent(db, owner_id=owner_two.id, name="Owner Two Agent")
        build_provider_config(db, owner_id=owner_one.id)
        session_record = session_service.upsert_chat_session(
            db,
            user_id=owner_one.id,
            session_type=session_service.SESSION_TYPE_AGENT,
            agent_id=agent_one.id,
            messages=[{"role": "user", "content": "Hello"}],
            assistant_reply="Owner one reply",
        )

    current_user = SimpleNamespace(id=owner_two.id, role=owner_two.role)
    headers = auth_headers(owner_two.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.agent_chat_service.call_provider_chat_completion"
    ) as mock_provider:
        response = client.post(
            f"/agents/{agent_two.id}/chat",
            headers=headers,
            json={
                "session_id": str(session_record.id),
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Owner one reply"},
                    {"role": "user", "content": "Other user tries to continue"},
                ],
            },
        )

    assert response.status_code == 404
    mock_provider.assert_not_called()


def test_orchestrator_routes_persists_session_and_can_continue(client):
    with SessionLocal() as db:
        owner = build_user(db, email_prefix="orchestrator-owner")

    current_user = SimpleNamespace(id=owner.id, role=owner.role)
    headers = auth_headers(owner.id)
    preview_result = SimpleNamespace(
        task_text="Summarize this task",
        recommended_agent=SimpleNamespace(agent_id=uuid.uuid4(), name="Routing Agent"),
        candidate_agents=[],
        confidence="high",
        reasons=["Matched workspace task."],
        active_skill_matches=[],
        note="Preview only, no execution.",
    )
    chat_results = [
        SimpleNamespace(
            agent_id=uuid.uuid4(),
            agent_name="Routing Agent",
            reply="Workspace reply one",
            provider="openai",
            model="gpt-4o-mini",
            prompt_skills_used=["Prompt Skill"],
            knowledge_skills_used=[],
            knowledge_truncated=False,
            warning=None,
        ),
        SimpleNamespace(
            agent_id=uuid.uuid4(),
            agent_name="Routing Agent",
            reply="Workspace reply two",
            provider="openai",
            model="gpt-4o-mini",
            prompt_skills_used=["Prompt Skill"],
            knowledge_skills_used=[],
            knowledge_truncated=False,
            warning=None,
        ),
    ]

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.orchestrator_service.agent_routing_service.preview_agent_routing",
        return_value=preview_result,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent",
        side_effect=chat_results,
    ), patch(
        "app.services.orchestrator_service.log_service.record_activity",
        return_value=None,
    ):
        response = client.post(
            "/orchestrator/chat",
            headers=headers,
            json={"task_text": "Summarize this task", "messages": []},
        )

    assert response.status_code == 200
    first_payload = response.json()
    assert first_payload["status"] == "routed"
    assert first_payload["session_id"] is not None
    session_id = first_payload["session_id"]

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user):
        response = client.get(f"/sessions/{session_id}", headers=headers)

    assert response.status_code == 200
    detail = response.json()
    assert detail["messages"][0]["content"] == "Summarize this task"
    assert detail["messages"][1]["content"] == "Workspace reply one"

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user), patch(
        "app.services.orchestrator_service.agent_routing_service.preview_agent_routing",
        return_value=preview_result,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent",
        side_effect=chat_results[1:],
    ), patch(
        "app.services.orchestrator_service.log_service.record_activity",
        return_value=None,
    ):
        response = client.post(
            "/orchestrator/chat",
            headers=headers,
            json={
                "session_id": session_id,
                "task_text": "Summarize this task",
                "messages": [
                    {"role": "user", "content": "Summarize this task"},
                    {"role": "assistant", "content": "Workspace reply one"},
                    {"role": "user", "content": "Continue"},
                ],
            },
        )

    assert response.status_code == 200
    assert response.json()["session_id"] == session_id

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user):
        response = client.get(f"/sessions/{session_id}", headers=headers)

    assert response.status_code == 200
    detail = response.json()
    assert len(detail["messages"]) == 4
    assert detail["messages"][-1]["content"] == "Workspace reply two"


def test_orchestrator_fallback_creates_session_and_blocks_other_user(client):
    with SessionLocal() as db:
        owner_one = build_user(db, email_prefix="workspace-owner")
        owner_two = build_user(db, email_prefix="workspace-other")
        session_record = session_service.upsert_chat_session(
            db,
            user_id=owner_one.id,
            session_type=session_service.SESSION_TYPE_ORCHESTRATOR,
            messages=[{"role": "user", "content": "Initial workspace task"}],
            assistant_reply="Fallback reply one",
        )

    current_user_one = SimpleNamespace(id=owner_one.id, role=owner_one.role)
    current_user_two = SimpleNamespace(id=owner_two.id, role=owner_two.role)
    headers_one = auth_headers(owner_one.id)
    headers_two = auth_headers(owner_two.id)
    fallback_preview = SimpleNamespace(
        task_text="Fallback task",
        recommended_agent=None,
        candidate_agents=[],
        confidence="low",
        reasons=["No strong keyword overlap found."],
        active_skill_matches=[],
        note="Preview only, no execution.",
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user_one), patch(
        "app.services.orchestrator_service.agent_routing_service.preview_agent_routing",
        return_value=fallback_preview,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent"
    ) as mock_chat, patch(
        "app.services.orchestrator_service.log_service.record_activity",
        return_value=None,
    ):
        response = client.post(
            "/orchestrator/chat",
            headers=headers_one,
            json={"task_text": "Fallback task", "messages": []},
        )

    assert response.status_code == 200
    first_payload = response.json()
    assert first_payload["status"] == "fallback"
    assert first_payload["session_id"] is not None
    session_id = first_payload["session_id"]
    mock_chat.assert_not_called()

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user_one):
        response = client.get(f"/sessions/{session_id}", headers=headers_one)

    assert response.status_code == 200
    detail = response.json()
    assert detail["messages"][-1]["content"].startswith("Maaf, saya tidak menemukan agent")

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user_one), patch(
        "app.services.orchestrator_service.agent_routing_service.preview_agent_routing",
        return_value=fallback_preview,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent"
    ) as mock_chat, patch(
        "app.services.orchestrator_service.log_service.record_activity",
        return_value=None,
    ):
        response = client.post(
            "/orchestrator/chat",
            headers=headers_one,
            json={
                "session_id": session_id,
                "task_text": "Fallback task",
                "messages": [
                    {"role": "user", "content": "Fallback task"},
                    {"role": "assistant", "content": detail["messages"][-1]["content"]},
                    {"role": "user", "content": "Continue"},
                ],
            },
        )

    assert response.status_code == 200
    assert response.json()["session_id"] == session_id
    mock_chat.assert_not_called()

    with patch("app.services.auth_service.get_current_active_user", return_value=current_user_two), patch(
        "app.services.orchestrator_service.agent_routing_service.preview_agent_routing",
        return_value=fallback_preview,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent"
    ) as mock_chat:
        response = client.post(
            "/orchestrator/chat",
            headers=headers_two,
            json={
                "session_id": session_id,
                "task_text": "Fallback task",
                "messages": [{"role": "user", "content": "Fallback task"}],
            },
        )

    assert response.status_code == 404
    mock_chat.assert_not_called()
