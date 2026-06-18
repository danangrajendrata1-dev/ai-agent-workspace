import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.security import create_access_token
from fastapi import HTTPException

from app.schemas.agent_chat import AgentChatRequest
from app.services.agent_chat_service import clear_agent_chat_rate_limiter, chat_with_agent


def auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    clear_agent_chat_rate_limiter()
    yield
    clear_agent_chat_rate_limiter()


@pytest.fixture(autouse=True)
def stub_session_persistence():
    with patch(
        "app.services.agent_chat_service.session_service.upsert_chat_session",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ):
        yield


def build_agent(*, owner_id: uuid.UUID, name: str = "Agent Chat"):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name=name,
        slug=name.lower().replace(" ", "-"),
        description="Chat-capable workspace agent.",
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


def build_skill(
    *,
    name: str,
    content: str,
    source_type: str = "manual",
    source_id: uuid.UUID | None = None,
    status: str = "active",
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        name=name,
        content=content,
        source_type=source_type,
        source_id=source_id,
        version_label=None,
        risk_level="low",
        status=status,
        deleted_at=None,
    )


def build_assignment(
    *,
    skill,
    created_at: datetime | None = None,
    is_enabled: bool = True,
    agent_id: uuid.UUID | None = None,
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        agent_id=agent_id or uuid.uuid4(),
        skill_id=skill.id,
        is_enabled=is_enabled,
        created_at=created_at or datetime.now(UTC),
        skill=skill,
    )


def build_github_import_data(
    *,
    skill_import_type: str,
    content_preview: str,
    status: str = "imported",
    safe_resource_paths: list[str] | None = None,
    risky_resource_paths: list[str] | None = None,
    resource_paths: list[str] | None = None,
    import_type: str = "skill",
) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "repo_url": "https://github.com/example/repo",
        "branch": "main",
        "commit_sha": "abc123",
        "import_type": import_type,
        "file_path": "SKILL.md",
        "content_preview": content_preview,
        "status": status,
        "review_notes": None,
        "skill_import_type": skill_import_type,
        "inspection_warnings": [],
        "inspection_errors": [],
        "resource_paths": resource_paths or [],
        "safe_resource_paths": safe_resource_paths or [],
        "risky_resource_paths": risky_resource_paths or [],
        "blocked_resource_paths": [],
        "has_executable_resources": False,
        "requires_review": False,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


def build_db():
    return SimpleNamespace(commit=lambda: None)


def test_chat_route_requires_authentication(client):
    response = client.post(
        f"/agents/{uuid.uuid4()}/chat",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )

    assert response.status_code == 401


def test_chat_route_rejects_whitespace_only_content(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_chat_service.chat_with_agent"
    ) as mock_chat:
        response = client.post(
            f"/agents/{uuid.uuid4()}/chat",
            headers=headers,
            json={"messages": [{"role": "user", "content": "   "}]},
        )

    assert response.status_code == 422
    mock_chat.assert_not_called()


def test_chat_route_rejects_invalid_role(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_chat_service.chat_with_agent"
    ) as mock_chat:
        response = client.post(
            f"/agents/{uuid.uuid4()}/chat",
            headers=headers,
            json={"messages": [{"role": "system", "content": "Hello"}]},
        )

    assert response.status_code == 422
    mock_chat.assert_not_called()


def test_chat_route_rejects_too_many_messages(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    messages = [{"role": "user", "content": f"Message {index + 1}"} for index in range(51)]

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_chat_service.chat_with_agent"
    ) as mock_chat:
        response = client.post(
            f"/agents/{uuid.uuid4()}/chat",
            headers=headers,
            json={"messages": messages},
        )

    assert response.status_code == 422
    mock_chat.assert_not_called()


def test_chat_route_rejects_overlong_message(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_chat_service.chat_with_agent"
    ) as mock_chat:
        response = client.post(
            f"/agents/{uuid.uuid4()}/chat",
            headers=headers,
            json={"messages": [{"role": "user", "content": "a" * 4001}]},
        )

    assert response.status_code == 422
    mock_chat.assert_not_called()


def test_service_returns_404_for_other_users_agent():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    payload = AgentChatRequest(messages=[{"role": "user", "content": "Hello"}])

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=None):
        with pytest.raises(Exception) as exc_info:
            chat_with_agent(
                db,
                owner_id=user_id,
                agent_id=uuid.uuid4(),
                payload=payload,
                current_user=user,
            )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404


def test_service_rejects_missing_provider_configuration():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    payload = AgentChatRequest(messages=[{"role": "user", "content": "Hello"}])

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
        return_value=[],
    ), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=None,
    ):
        with pytest.raises(Exception) as exc_info:
            chat_with_agent(
                db,
                owner_id=user_id,
                agent_id=agent.id,
                payload=payload,
                current_user=user,
            )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No LLM provider configured for this agent"


def test_service_rejects_missing_api_key():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    payload = AgentChatRequest(messages=[{"role": "user", "content": "Hello"}])
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
        return_value=[],
    ), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=setting,
    ), patch(
        "app.services.agent_chat_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=None,
    ):
        with pytest.raises(Exception) as exc_info:
            chat_with_agent(
                db,
                owner_id=user_id,
                agent_id=agent.id,
                payload=payload,
                current_user=user,
            )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No API key found. Please configure your provider first."


def test_service_rejects_unsupported_provider():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    payload = AgentChatRequest(messages=[{"role": "user", "content": "Hello"}])
    setting = SimpleNamespace(preferred_provider="custom", preferred_model="gpt-4o-mini")

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
        return_value=[],
    ), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=setting,
    ):
        with pytest.raises(HTTPException) as exc_info:
            chat_with_agent(
                db,
                owner_id=user_id,
                agent_id=agent.id,
                payload=payload,
                current_user=user,
            )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Provider not supported"


def test_service_success_uses_prompt_skill_content_and_ignores_other_skills():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    prompt_skill = build_skill(
        name="Prompt Skill",
        content="You are a careful workspace assistant.",
    )
    knowledge_skill = build_skill(
        name="Knowledge Skill",
        content="Knowledge content should never reach the prompt.",
        source_type="github",
        source_id=uuid.uuid4(),
    )
    tool_skill = build_skill(
        name="Tool Skill",
        content="Tool content should never reach the prompt.",
        source_type="github",
        source_id=uuid.uuid4(),
    )
    workflow_skill = build_skill(
        name="Workflow Skill",
        content="Workflow content should never reach the prompt.",
        source_type="github",
        source_id=uuid.uuid4(),
    )
    prompt_assignment = build_assignment(
        skill=prompt_skill,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    knowledge_assignment = build_assignment(
        skill=knowledge_skill,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    tool_assignment = build_assignment(
        skill=tool_skill,
        created_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    workflow_assignment = build_assignment(
        skill=workflow_skill,
        created_at=datetime(2026, 1, 4, tzinfo=UTC),
    )
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")
    api_key_record = SimpleNamespace(encrypted_api_key="encrypted")
    captured = {}
    import_data_map = {
        knowledge_skill.source_id: build_github_import_data(
            skill_import_type="markdown_instruction",
            content_preview="Knowledge instruction with reference files.",
            safe_resource_paths=["docs/reference.md"],
        ),
        tool_skill.source_id: build_github_import_data(
            skill_import_type="manifest_skill",
            content_preview="Tool instruction with a risky resource path.",
            risky_resource_paths=["tools/run.sh"],
        ),
        workflow_skill.source_id: build_github_import_data(
            skill_import_type="markdown_instruction",
            content_preview="Workflow instruction for automation.",
            safe_resource_paths=["docs/overview.md"],
            resource_paths=["workflows/main.yaml"],
        ),
    }

    def fake_serialize_github_import(github_import):
        return SimpleNamespace(model_dump=lambda: import_data_map[github_import.id])

    def fake_call_provider_chat_completion(**kwargs):
        captured.update(kwargs)
        return {
            "reply": "Assistant reply",
            "prompt_tokens": 11,
            "completion_tokens": 7,
        }

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=setting,
    ), patch(
        "app.services.agent_chat_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=api_key_record,
    ), patch(
        "app.services.agent_chat_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
        return_value=[
            workflow_assignment,
            tool_assignment,
            knowledge_assignment,
            prompt_assignment,
        ],
    ), patch(
        "app.services.agent_chat_service.github_import_repository.get_by_id_for_owner",
        side_effect=lambda _db, import_id, owner_id: SimpleNamespace(id=import_id),
    ), patch(
        "app.services.agent_chat_service.serialize_github_import",
        side_effect=fake_serialize_github_import,
    ), patch(
        "app.services.agent_chat_service.call_provider_chat_completion",
        side_effect=fake_call_provider_chat_completion,
    ), patch(
        "app.services.agent_chat_service.log_service.record_activity",
        return_value=None,
    ):
        result = chat_with_agent(
            db,
            owner_id=user_id,
            agent_id=agent.id,
            payload=AgentChatRequest(messages=[{"role": "user", "content": "Hello"}]),
            current_user=user,
        )

    assert result.reply == "Assistant reply"
    assert result.provider == "openai"
    assert result.model == "gpt-4o-mini"
    assert result.prompt_skills_used == ["Prompt Skill"]
    assert result.knowledge_skills_used == ["Knowledge Skill"]
    assert result.knowledge_truncated is False
    assert result.warning is None
    assert captured["system_prompt"] == (
        "You are a careful workspace assistant.\n\n"
        "--- KNOWLEDGE CONTEXT ---\n"
        "[Knowledge Skill]\n"
        "Knowledge content should never reach the prompt.\n"
        "--- END KNOWLEDGE CONTEXT ---"
    )
    assert "Knowledge content should never reach the prompt." in captured["system_prompt"]
    assert "Tool content should never reach the prompt." not in captured["system_prompt"]
    assert "Workflow content should never reach the prompt." not in captured["system_prompt"]


def test_service_applies_imported_prompt_skill_content_to_system_prompt():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    prompt_skill = build_skill(
        name="Prompt Skill",
        content="You are a careful workspace assistant.",
        source_type="github",
        source_id=uuid.uuid4(),
        status="inactive",
    )
    assignment = build_assignment(
        skill=prompt_skill,
        agent_id=agent.id,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")
    api_key_record = SimpleNamespace(encrypted_api_key="encrypted")
    captured = {}
    recorded = {}
    import_data_map = {
        prompt_skill.source_id: build_github_import_data(
            skill_import_type="markdown_instruction",
            content_preview="You are a careful workspace assistant.",
            status="imported",
        )
    }

    def fake_serialize_github_import(github_import):
        return SimpleNamespace(model_dump=lambda: import_data_map[github_import.id])

    def fake_call_provider_chat_completion(**kwargs):
        captured.update(kwargs)
        return {
            "reply": "Assistant reply",
            "prompt_tokens": 5,
            "completion_tokens": 2,
        }

    def fake_record_activity(*args, **kwargs):
        recorded.update(kwargs)
        return None

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=setting,
    ), patch(
        "app.services.agent_chat_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=api_key_record,
    ), patch(
        "app.services.agent_chat_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
        return_value=[assignment],
    ), patch(
        "app.services.agent_chat_service.github_import_repository.get_by_id_for_owner",
        return_value=SimpleNamespace(id=prompt_skill.source_id),
    ), patch(
        "app.services.agent_chat_service.serialize_github_import",
        side_effect=fake_serialize_github_import,
    ), patch(
        "app.services.agent_chat_service.call_provider_chat_completion",
        side_effect=fake_call_provider_chat_completion,
    ), patch(
        "app.services.agent_chat_service.log_service.record_activity",
        side_effect=fake_record_activity,
    ):
        result = chat_with_agent(
            db,
            owner_id=user_id,
            agent_id=agent.id,
            payload=AgentChatRequest(messages=[{"role": "user", "content": "Hello"}]),
            current_user=user,
        )

    assert result.prompt_skills_used == ["Prompt Skill"]
    assert result.knowledge_skills_used == []
    assert result.knowledge_truncated is False
    assert result.warning is None
    assert captured["system_prompt"] == "You are a careful workspace assistant."
    assert recorded["metadata_json"]["prompt_skill_count"] == 1
    assert "You are a careful workspace assistant." not in str(recorded["metadata_json"])
    assert "Prompt Skill" not in str(recorded["metadata_json"])


def test_service_ignores_non_approved_imported_prompt_skill_in_chat():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    prompt_skill = build_skill(
        name="Prompt Skill",
        content="You are a careful workspace assistant.",
        source_type="github",
        source_id=uuid.uuid4(),
        status="inactive",
    )
    assignment = build_assignment(
        skill=prompt_skill,
        agent_id=agent.id,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")
    api_key_record = SimpleNamespace(encrypted_api_key="encrypted")
    captured = {}

    def fake_call_provider_chat_completion(**kwargs):
        captured.update(kwargs)
        return {
            "reply": "Assistant reply",
            "prompt_tokens": 5,
            "completion_tokens": 2,
        }

    for import_status in ("preview", "rejected", "disabled"):
        import_data_map = {
            prompt_skill.source_id: build_github_import_data(
                skill_import_type="markdown_instruction",
                content_preview="You are a careful workspace assistant.",
                status=import_status,
            )
        }

        def fake_serialize_github_import(github_import, *, _import_data_map=import_data_map):
            return SimpleNamespace(model_dump=lambda: _import_data_map[github_import.id])

        with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
            "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
            return_value=setting,
        ), patch(
            "app.services.agent_chat_service.model_provider_api_key_repository.get_by_owner_and_provider",
            return_value=api_key_record,
        ), patch(
            "app.services.agent_chat_service.decrypt_api_key",
            return_value="decrypted-api-key",
        ), patch(
            "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
            return_value=[assignment],
        ), patch(
            "app.services.agent_chat_service.github_import_repository.get_by_id_for_owner",
            return_value=SimpleNamespace(id=prompt_skill.source_id),
        ), patch(
            "app.services.agent_chat_service.serialize_github_import",
            side_effect=fake_serialize_github_import,
        ), patch(
            "app.services.agent_chat_service.call_provider_chat_completion",
            side_effect=fake_call_provider_chat_completion,
        ), patch(
            "app.services.agent_chat_service.log_service.record_activity",
            return_value=None,
        ):
            result = chat_with_agent(
                db,
                owner_id=user_id,
                agent_id=agent.id,
                payload=AgentChatRequest(messages=[{"role": "user", "content": "Hello"}]),
                current_user=user,
            )

        assert result.prompt_skills_used == []
        assert result.knowledge_skills_used == []
        assert captured["system_prompt"] == "You are a helpful AI assistant."


def test_service_ignores_prompt_skill_from_other_owner_and_other_agent():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    prompt_skill = build_skill(
        name="Prompt Skill",
        content="You are a careful workspace assistant.",
        source_type="github",
        source_id=uuid.uuid4(),
        status="inactive",
    )
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")
    api_key_record = SimpleNamespace(encrypted_api_key="encrypted")
    captured = {}

    def fake_call_provider_chat_completion(**kwargs):
        captured.update(kwargs)
        return {
            "reply": "Assistant reply",
            "prompt_tokens": 5,
            "completion_tokens": 2,
        }

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=setting,
    ), patch(
        "app.services.agent_chat_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=api_key_record,
    ), patch(
        "app.services.agent_chat_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
        return_value=[],
    ), patch(
        "app.services.agent_chat_service.github_import_repository.get_by_id_for_owner",
        return_value=None,
    ), patch(
        "app.services.agent_chat_service.call_provider_chat_completion",
        side_effect=fake_call_provider_chat_completion,
    ), patch(
        "app.services.agent_chat_service.log_service.record_activity",
        return_value=None,
    ):
        result = chat_with_agent(
            db,
            owner_id=user_id,
            agent_id=agent.id,
            payload=AgentChatRequest(messages=[{"role": "user", "content": "Hello"}]),
            current_user=user,
        )

    assert result.prompt_skills_used == []
    assert result.knowledge_skills_used == []
    assert captured["system_prompt"] == "You are a helpful AI assistant."


def test_service_uses_default_system_prompt_when_no_prompt_skills_active():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    tool_skill = build_skill(
        name="Tool Skill",
        content="Tool content should be ignored.",
        source_type="github",
        source_id=uuid.uuid4(),
    )
    assignment = build_assignment(
        skill=tool_skill,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")
    api_key_record = SimpleNamespace(encrypted_api_key="encrypted")
    captured = {}
    import_data_map = {
        tool_skill.source_id: build_github_import_data(
            skill_import_type="manifest_skill",
            content_preview="Tool content should be ignored.",
            risky_resource_paths=["tools/run.sh"],
        )
    }

    def fake_call_provider_chat_completion(**kwargs):
        captured.update(kwargs)
        return {
            "reply": "Assistant reply",
            "prompt_tokens": None,
            "completion_tokens": None,
        }

    def fake_serialize_github_import(github_import):
        return SimpleNamespace(model_dump=lambda: import_data_map[github_import.id])

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=setting,
    ), patch(
        "app.services.agent_chat_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=api_key_record,
        ), patch(
            "app.services.agent_chat_service.decrypt_api_key",
            return_value="decrypted-api-key",
        ), patch(
            "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
            return_value=[assignment],
        ), patch(
            "app.services.agent_chat_service.github_import_repository.get_by_id_for_owner",
            side_effect=lambda _db, import_id, owner_id: SimpleNamespace(id=import_id),
        ), patch(
            "app.services.agent_chat_service.serialize_github_import",
            side_effect=fake_serialize_github_import,
        ), patch(
            "app.services.agent_chat_service.call_provider_chat_completion",
            side_effect=fake_call_provider_chat_completion,
        ), patch(
            "app.services.agent_chat_service.log_service.record_activity",
        return_value=None,
    ):
        result = chat_with_agent(
            db,
            owner_id=user_id,
            agent_id=agent.id,
            payload=AgentChatRequest(messages=[{"role": "user", "content": "Hello"}]),
            current_user=user,
        )

    assert result.prompt_skills_used == []
    assert result.knowledge_skills_used == []
    assert result.knowledge_truncated is False
    assert result.warning is None
    assert captured["system_prompt"] == "You are a helpful AI assistant."
    assert "--- KNOWLEDGE CONTEXT ---" not in captured["system_prompt"]


def test_service_multiple_knowledge_skills_are_deterministic():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    prompt_skill = build_skill(
        name="Prompt Skill",
        content="You are a careful workspace assistant.",
    )
    knowledge_a = build_skill(
        name="Alpha Knowledge",
        content="Alpha knowledge content.",
        source_type="github",
        source_id=uuid.uuid4(),
    )
    knowledge_b = build_skill(
        name="Beta Knowledge",
        content="Beta knowledge content.",
        source_type="github",
        source_id=uuid.uuid4(),
    )
    prompt_assignment = build_assignment(
        skill=prompt_skill,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    knowledge_b_assignment = build_assignment(
        skill=knowledge_b,
        created_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    knowledge_a_assignment = build_assignment(
        skill=knowledge_a,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")
    api_key_record = SimpleNamespace(encrypted_api_key="encrypted")
    captured = {}
    import_data_map = {
        knowledge_a.source_id: build_github_import_data(
            skill_import_type="markdown_instruction",
            content_preview="Alpha knowledge instruction.",
            safe_resource_paths=["docs/alpha.md"],
        ),
        knowledge_b.source_id: build_github_import_data(
            skill_import_type="markdown_instruction",
            content_preview="Beta knowledge instruction.",
            safe_resource_paths=["docs/beta.md"],
        ),
    }

    def fake_serialize_github_import(github_import):
        return SimpleNamespace(model_dump=lambda: import_data_map[github_import.id])

    def fake_call_provider_chat_completion(**kwargs):
        captured.update(kwargs)
        return {
            "reply": "Assistant reply",
            "prompt_tokens": None,
            "completion_tokens": None,
        }

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=setting,
    ), patch(
        "app.services.agent_chat_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=api_key_record,
    ), patch(
        "app.services.agent_chat_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
        return_value=[prompt_assignment, knowledge_b_assignment, knowledge_a_assignment],
    ), patch(
        "app.services.agent_chat_service.github_import_repository.get_by_id_for_owner",
        side_effect=lambda _db, import_id, owner_id: SimpleNamespace(id=import_id),
    ), patch(
        "app.services.agent_chat_service.serialize_github_import",
        side_effect=fake_serialize_github_import,
    ), patch(
        "app.services.agent_chat_service.call_provider_chat_completion",
        side_effect=fake_call_provider_chat_completion,
    ), patch(
        "app.services.agent_chat_service.log_service.record_activity",
        return_value=None,
    ):
        result = chat_with_agent(
            db,
            owner_id=user_id,
            agent_id=agent.id,
            payload=AgentChatRequest(messages=[{"role": "user", "content": "Hello"}]),
            current_user=user,
        )

    assert result.knowledge_skills_used == ["Alpha Knowledge", "Beta Knowledge"]
    assert result.knowledge_truncated is False
    knowledge_block = captured["system_prompt"].split("--- KNOWLEDGE CONTEXT ---\n", 1)[1].rsplit(
        "\n--- END KNOWLEDGE CONTEXT ---",
        1,
    )[0]
    assert knowledge_block.index("[Alpha Knowledge]") < knowledge_block.index("[Beta Knowledge]")


def test_service_truncates_knowledge_context_at_limit():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    prompt_skill = build_skill(
        name="Prompt Skill",
        content="You are a careful workspace assistant.",
    )
    long_content = "L" * 5000
    knowledge_a = build_skill(
        name="Knowledge A",
        content=long_content,
        source_type="github",
        source_id=uuid.uuid4(),
    )
    knowledge_b = build_skill(
        name="Knowledge B",
        content=long_content,
        source_type="github",
        source_id=uuid.uuid4(),
    )
    prompt_assignment = build_assignment(
        skill=prompt_skill,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    knowledge_a_assignment = build_assignment(
        skill=knowledge_a,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    knowledge_b_assignment = build_assignment(
        skill=knowledge_b,
        created_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")
    api_key_record = SimpleNamespace(encrypted_api_key="encrypted")
    captured = {}
    import_data_map = {
        knowledge_a.source_id: build_github_import_data(
            skill_import_type="markdown_instruction",
            content_preview="Knowledge A instruction.",
            safe_resource_paths=["docs/a.md"],
        ),
        knowledge_b.source_id: build_github_import_data(
            skill_import_type="markdown_instruction",
            content_preview="Knowledge B instruction.",
            safe_resource_paths=["docs/b.md"],
        ),
    }

    def fake_serialize_github_import(github_import):
        return SimpleNamespace(model_dump=lambda: import_data_map[github_import.id])

    def fake_call_provider_chat_completion(**kwargs):
        captured.update(kwargs)
        return {
            "reply": "Assistant reply",
            "prompt_tokens": None,
            "completion_tokens": None,
        }

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=setting,
    ), patch(
        "app.services.agent_chat_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=api_key_record,
    ), patch(
        "app.services.agent_chat_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
        return_value=[prompt_assignment, knowledge_a_assignment, knowledge_b_assignment],
    ), patch(
        "app.services.agent_chat_service.github_import_repository.get_by_id_for_owner",
        side_effect=lambda _db, import_id, owner_id: SimpleNamespace(id=import_id),
    ), patch(
        "app.services.agent_chat_service.serialize_github_import",
        side_effect=fake_serialize_github_import,
    ), patch(
        "app.services.agent_chat_service.call_provider_chat_completion",
        side_effect=fake_call_provider_chat_completion,
    ), patch(
        "app.services.agent_chat_service.log_service.record_activity",
        return_value=None,
    ):
        result = chat_with_agent(
            db,
            owner_id=user_id,
            agent_id=agent.id,
            payload=AgentChatRequest(messages=[{"role": "user", "content": "Hello"}]),
            current_user=user,
        )

    assert result.knowledge_truncated is True
    assert result.warning == "Knowledge context truncated due to length limit"
    knowledge_block = captured["system_prompt"].split("--- KNOWLEDGE CONTEXT ---\n", 1)[1].rsplit(
        "\n--- END KNOWLEDGE CONTEXT ---",
        1,
    )[0]
    assert len(knowledge_block) <= 8000
    assert "[Knowledge A]" in knowledge_block
    assert "Knowledge context truncated due to length limit" in result.warning


def test_service_skips_empty_knowledge_skill_content():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    prompt_skill = build_skill(
        name="Prompt Skill",
        content="You are a careful workspace assistant.",
    )
    empty_knowledge = build_skill(
        name="Empty Knowledge",
        content="   ",
        source_type="github",
        source_id=uuid.uuid4(),
    )
    prompt_assignment = build_assignment(
        skill=prompt_skill,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    knowledge_assignment = build_assignment(
        skill=empty_knowledge,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")
    api_key_record = SimpleNamespace(encrypted_api_key="encrypted")
    captured = {}
    import_data_map = {
        empty_knowledge.source_id: build_github_import_data(
            skill_import_type="markdown_instruction",
            content_preview="Empty knowledge instruction.",
            safe_resource_paths=["docs/empty.md"],
        )
    }

    def fake_serialize_github_import(github_import):
        return SimpleNamespace(model_dump=lambda: import_data_map[github_import.id])

    def fake_call_provider_chat_completion(**kwargs):
        captured.update(kwargs)
        return {
            "reply": "Assistant reply",
            "prompt_tokens": None,
            "completion_tokens": None,
        }

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=setting,
    ), patch(
        "app.services.agent_chat_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=api_key_record,
    ), patch(
        "app.services.agent_chat_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
        return_value=[prompt_assignment, knowledge_assignment],
    ), patch(
        "app.services.agent_chat_service.github_import_repository.get_by_id_for_owner",
        side_effect=lambda _db, import_id, owner_id: SimpleNamespace(id=import_id),
    ), patch(
        "app.services.agent_chat_service.serialize_github_import",
        side_effect=fake_serialize_github_import,
    ), patch(
        "app.services.agent_chat_service.call_provider_chat_completion",
        side_effect=fake_call_provider_chat_completion,
    ), patch(
        "app.services.agent_chat_service.log_service.record_activity",
        return_value=None,
    ):
        result = chat_with_agent(
            db,
            owner_id=user_id,
            agent_id=agent.id,
            payload=AgentChatRequest(messages=[{"role": "user", "content": "Hello"}]),
            current_user=user,
        )

    assert result.knowledge_skills_used == []
    assert result.knowledge_truncated is False
    assert result.warning == "Skipped knowledge skill 'Empty Knowledge' because it has no usable content."
    assert "--- KNOWLEDGE CONTEXT ---" not in captured["system_prompt"]


def test_service_skips_empty_prompt_skill_content_with_warning():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    empty_prompt_skill = build_skill(
        name="Empty Prompt",
        content="   ",
    )
    assignment = build_assignment(
        skill=empty_prompt_skill,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")
    api_key_record = SimpleNamespace(encrypted_api_key="encrypted")
    captured = {}

    def fake_call_provider_chat_completion(**kwargs):
        captured.update(kwargs)
        return {
            "reply": "Assistant reply",
            "prompt_tokens": None,
            "completion_tokens": None,
        }

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=setting,
    ), patch(
        "app.services.agent_chat_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=api_key_record,
    ), patch(
        "app.services.agent_chat_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
        return_value=[assignment],
    ), patch(
        "app.services.agent_chat_service.call_provider_chat_completion",
        side_effect=fake_call_provider_chat_completion,
    ), patch(
        "app.services.agent_chat_service.log_service.record_activity",
        return_value=None,
    ):
        result = chat_with_agent(
            db,
            owner_id=user_id,
            agent_id=agent.id,
            payload=AgentChatRequest(messages=[{"role": "user", "content": "Hello"}]),
            current_user=user,
        )

    assert result.prompt_skills_used == []
    assert result.warning == "Skipped prompt skill 'Empty Prompt' because it has no usable content."
    assert captured["system_prompt"] == "You are a helpful AI assistant."


def test_service_success_response_does_not_expose_raw_provider_response_or_api_key():
    db = build_db()
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id, role="user")
    agent = build_agent(owner_id=user_id)
    prompt_skill = build_skill(
        name="Prompt Skill",
        content="You are a careful workspace assistant.",
    )
    assignment = build_assignment(
        skill=prompt_skill,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")
    api_key_record = SimpleNamespace(encrypted_api_key="encrypted-secret-value")
    recorded = {}

    def fake_call_provider_chat_completion(**kwargs):
        return {
            "reply": "Assistant reply",
            "prompt_tokens": 9,
            "completion_tokens": 4,
            "raw_response": {"api_key": "should-not-leak", "choices": [{"message": {"content": "leak"}}]},
        }

    def fake_record_activity(*args, **kwargs):
        recorded.update(kwargs)
        return None

    with patch("app.services.agent_chat_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=setting,
    ), patch(
        "app.services.agent_chat_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=api_key_record,
    ), patch(
        "app.services.agent_chat_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
        return_value=[assignment],
    ), patch(
        "app.services.agent_chat_service.call_provider_chat_completion",
        side_effect=fake_call_provider_chat_completion,
    ), patch(
        "app.services.agent_chat_service.log_service.record_activity",
        side_effect=fake_record_activity,
    ):
        result = chat_with_agent(
            db,
            owner_id=user_id,
            agent_id=agent.id,
            payload=AgentChatRequest(messages=[{"role": "user", "content": "Hello"}]),
            current_user=user,
        )

    assert result.reply == "Assistant reply"
    assert result.provider == "openai"
    assert result.model == "gpt-4o-mini"
    assert result.prompt_skills_used == ["Prompt Skill"]
    assert result.knowledge_skills_used == []
    assert result.knowledge_truncated is False
    assert "raw_response" not in result.model_dump()
    assert "encrypted-secret-value" not in result.model_dump_json()
    assert "decrypted-api-key" not in result.model_dump_json()
    assert recorded["metadata_json"]["provider"] == "openai"
    assert recorded["metadata_json"]["model"] == "gpt-4o-mini"
    assert recorded["metadata_json"]["prompt_skill_count"] == 1
    assert recorded["metadata_json"]["knowledge_skill_count"] == 0
    assert recorded["metadata_json"]["knowledge_truncated"] is False
    assert "raw_response" not in recorded["metadata_json"]
    assert "encrypted-secret-value" not in str(recorded["metadata_json"])
    assert "Prompt Skill" not in str(recorded["metadata_json"])


def test_chat_route_rate_limit_blocks_21st_request(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    headers = auth_headers(user.id)
    agent = build_agent(owner_id=user.id)
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")
    api_key_record = SimpleNamespace(encrypted_api_key="encrypted")

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_chat_service.agent_repository.get_by_id",
        return_value=agent,
    ), patch(
        "app.services.agent_chat_service.model_provider_setting_repository.get_by_owner_id",
        return_value=setting,
    ), patch(
        "app.services.agent_chat_service.model_provider_api_key_repository.get_by_owner_and_provider",
        return_value=api_key_record,
    ), patch(
        "app.services.agent_chat_service.decrypt_api_key",
        return_value="decrypted-api-key",
    ), patch(
        "app.services.agent_chat_service.agent_skill_repository.list_agent_skills",
        return_value=[],
    ), patch(
        "app.services.agent_chat_service.call_provider_chat_completion",
        return_value={
            "reply": "Assistant reply",
            "prompt_tokens": 3,
            "completion_tokens": 2,
        },
    ), patch(
        "app.services.agent_chat_service.log_service.record_activity",
        return_value=None,
    ):
        statuses = []
        for _ in range(21):
            response = client.post(
                f"/agents/{agent.id}/chat",
                headers=headers,
                json={"messages": [{"role": "user", "content": "Hello"}]},
            )
            statuses.append(response.status_code)

    assert statuses[:20] == [200] * 20
    assert statuses[20] == 429
