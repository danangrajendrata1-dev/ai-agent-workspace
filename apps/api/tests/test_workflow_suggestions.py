import uuid
from datetime import UTC, datetime
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.database import SessionLocal
from app.repositories import workflow_execution_repository
from app.schemas.agent_chat import AgentChatRequest, WorkflowSuggestion
from app.services.agent_chat_service import chat_with_agent
from app.services.orchestrator_service import orchestrate_workspace_chat
from app.services.workflow_suggestion_service import get_workflow_suggestions_for_agent

from .test_sessions import auth_headers


def build_db():
    return SimpleNamespace(commit=lambda: None)


def build_user(role: str = "user"):
    return SimpleNamespace(id=uuid.uuid4(), role=role)


def build_agent(owner_id: uuid.UUID, name: str = "Workflow Agent"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name=name,
        slug=name.lower().replace(" ", "-"),
        description="Helper agent.",
        role_description="Helpful workspace assistant.",
        status="active",
        deleted_at=None,
    )


def build_workflow_skill(*, title: str, content: str = "Workflow skill content."):
    skill_id = uuid.uuid4()
    skill = SimpleNamespace(
        id=skill_id,
        name=title,
        title=title,
        content=content,
        instruction_text=content,
        prompt=content,
        text=content,
        skill_type="workflow_skill",
        status="active",
        deleted_at=None,
    )
    return SimpleNamespace(
        id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        skill_id=skill_id,
        is_enabled=True,
        created_at=datetime.now(UTC),
        skill=skill,
    )


def build_imported_workflow_skill(*, title: str, content: str = "Workflow skill content.", status: str = "active"):
    assignment = build_workflow_skill(title=title, content=content)
    assignment.skill.source_type = "github"
    assignment.skill.source_id = uuid.uuid4()
    assignment.skill.status = status
    assignment.skill.risk_level = "low"
    assignment.skill.created_at = datetime.now(UTC)
    assignment.skill.updated_at = assignment.skill.created_at
    return assignment


def build_github_import_record(*, import_id: uuid.UUID, owner_id: uuid.UUID, status: str = "imported", content_preview: str):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=import_id,
        owner_id=owner_id,
        repo_url="https://github.com/example/repo",
        branch="main",
        commit_sha="abc123",
        import_type="skill",
        file_path="skills/workflow/SKILL.md",
        content_preview=content_preview,
        status=status,
        review_notes=None,
        created_at=now,
        updated_at=now,
    )


def build_prompt_skill(*, title: str = "Prompt Skill"):
    skill_id = uuid.uuid4()
    skill = SimpleNamespace(
        id=skill_id,
        name=title,
        title=title,
        content="Prompt content.",
        skill_type="prompt_skill",
        status="active",
        deleted_at=None,
    )
    return SimpleNamespace(
        id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        skill_id=skill_id,
        is_enabled=True,
        created_at=datetime.now(UTC),
        skill=skill,
    )


def build_template(*, enabled: bool = True, version: str = "1.0", webhook_url: str = "https://workflow.example.org/webhook/generate-pdf"):
    return {
        "id": "generate_pdf",
        "name": "Generate PDF",
        "description": "Membuat file PDF dari teks",
        "webhook_url": webhook_url,
        "input_schema": {"title": "string", "content": "string"},
        "output_type": "json",
        "enabled": enabled,
        "template_version": version,
        "risk_level": "medium",
        "max_payload_bytes": 10000,
    }


def build_binding(*, skill_id: uuid.UUID, template_version: str = "1.0"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        skill_id=skill_id,
        template_id="generate_pdf",
        template_version=template_version,
        created_at=datetime.now(UTC),
    )


def build_consent(*, template_version: str = "1.0"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        template_id="generate_pdf",
        template_version=template_version,
        consented_at=datetime.now(UTC),
    )


@contextmanager
def patch_template_registry(*, enabled: bool = True, version: str = "1.0", webhook_url: str = "https://workflow.example.org/webhook/generate-pdf"):
    template = build_template(enabled=enabled, version=version, webhook_url=webhook_url)
    with patch(
        "app.services.workflow_suggestion_service.get_workflow_templates",
        return_value=[{
            "id": template["id"],
            "name": template["name"],
            "description": template["description"],
            "input_schema": template["input_schema"],
            "output_type": template["output_type"],
            "enabled": template["enabled"],
            "template_version": template["template_version"],
            "risk_level": template["risk_level"],
            "max_payload_bytes": template["max_payload_bytes"],
        }],
    ), patch(
        "app.services.workflow_suggestion_service.get_workflow_template",
        return_value=template,
    ), patch(
        "app.services.workflow_suggestion_service.validate_safe_webhook_url",
        return_value=(webhook_url.startswith("https://"), None),
    ):
        yield


def test_workflow_suggestions_helper_returns_executable_match_when_binding_and_consent_exist():
    db = build_db()
    user = build_user()
    agent = build_agent(user.id)
    skill = build_workflow_skill(title="PDF Generator", content="Generate PDF files from task text.")
    binding = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user.id,
        skill_id=skill.skill_id,
        template_id="generate_pdf",
        template_version="1.0",
        created_at=datetime.now(UTC),
    )
    consent = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user.id,
        template_id="generate_pdf",
        template_version="1.0",
        consented_at=datetime.now(UTC),
    )

    with patch("app.services.workflow_suggestion_service.skill_service.list_active_agent_skills", return_value=[skill]), patch(
        "app.services.workflow_suggestion_service.workflow_skill_binding_repository.list_bindings",
        return_value=[binding],
    ), patch(
        "app.services.workflow_suggestion_service.workflow_consent_repository.list_consents",
        return_value=[consent],
    ), patch_template_registry():
        suggestions = get_workflow_suggestions_for_agent(
            db,
            user=user,
            agent_id=agent.id,
            task_text="Please generate a PDF for the report",
        )

    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion.template_id == "generate_pdf"
    assert suggestion.skill_id == str(skill.skill_id)
    assert suggestion.consent_required is False
    assert suggestion.binding_exists is True
    assert suggestion.execution_available is True


def test_workflow_suggestions_helper_returns_match_for_imported_workflow_skill():
    db = build_db()
    user = build_user()
    agent = build_agent(user.id)
    assignment = build_imported_workflow_skill(title="PDF Generator", content="Generate PDF files from task text.")
    assignment.agent_id = agent.id
    binding = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user.id,
        skill_id=assignment.skill_id,
        template_id="generate_pdf",
        template_version="1.0",
        created_at=datetime.now(UTC),
    )
    consent = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user.id,
        template_id="generate_pdf",
        template_version="1.0",
        consented_at=datetime.now(UTC),
    )
    github_import = build_github_import_record(
        import_id=assignment.skill.source_id,
        owner_id=user.id,
        status="imported",
        content_preview="Workflow instruction to generate PDF files from task text.",
    )

    with patch("app.services.skill_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.skill_service.agent_skill_repository.list_agent_skills",
        return_value=[assignment],
    ), patch(
        "app.services.skill_service.github_import_repository.list_imports",
        return_value=[github_import],
    ), patch(
        "app.services.workflow_suggestion_service.workflow_skill_binding_repository.list_bindings",
        return_value=[binding],
    ), patch(
        "app.services.workflow_suggestion_service.workflow_consent_repository.list_consents",
        return_value=[consent],
    ), patch_template_registry():
        suggestions = get_workflow_suggestions_for_agent(
            db,
            user=user,
            agent_id=agent.id,
            task_text="Please generate a PDF for the report",
        )

    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion.template_id == "generate_pdf"
    assert suggestion.skill_id == str(assignment.skill_id)
    assert suggestion.execution_available is True


def test_workflow_suggestions_helper_ignores_non_approved_imported_workflow_skill():
    db = build_db()
    user = build_user()
    agent = build_agent(user.id)
    assignment = build_imported_workflow_skill(title="PDF Generator", content="Generate PDF files from task text.")
    assignment.agent_id = agent.id

    for import_status in ("preview", "rejected", "disabled"):
        github_import = build_github_import_record(
            import_id=assignment.skill.source_id,
            owner_id=user.id,
            status=import_status,
            content_preview="Workflow instruction to generate PDF files from task text.",
        )
        with patch("app.services.skill_service.agent_repository.get_by_id", return_value=agent), patch(
            "app.services.skill_service.agent_skill_repository.list_agent_skills",
            return_value=[assignment],
        ), patch(
            "app.services.skill_service.github_import_repository.list_imports",
            return_value=[github_import],
        ), patch(
            "app.services.workflow_suggestion_service.workflow_skill_binding_repository.list_bindings",
            return_value=[],
        ), patch(
            "app.services.workflow_suggestion_service.workflow_consent_repository.list_consents",
            return_value=[],
        ), patch_template_registry():
            suggestions = get_workflow_suggestions_for_agent(
                db,
                user=user,
                agent_id=agent.id,
                task_text="Please generate a PDF for the report",
            )

        assert suggestions == []


def test_workflow_suggestions_helper_ignores_non_workflow_skill_types():
    db = build_db()
    user = build_user()
    agent = build_agent(user.id)
    prompt_skill = build_prompt_skill(title="Prompt Skill")
    knowledge_skill = build_workflow_skill(title="Knowledge Skill", content="Knowledge content.")
    knowledge_skill.skill.skill_type = "knowledge_skill"
    tool_skill = build_workflow_skill(title="Tool Skill", content="Tool content.")
    tool_skill.skill.skill_type = "tool_skill"

    with patch("app.services.skill_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.skill_service.agent_skill_repository.list_agent_skills",
        return_value=[prompt_skill, knowledge_skill, tool_skill],
    ), patch(
        "app.services.skill_service.github_import_repository.list_imports",
        return_value=[],
    ), patch(
        "app.services.workflow_suggestion_service.workflow_skill_binding_repository.list_bindings",
        return_value=[],
    ), patch(
        "app.services.workflow_suggestion_service.workflow_consent_repository.list_consents",
        return_value=[],
    ), patch_template_registry():
        suggestions = get_workflow_suggestions_for_agent(
            db,
            user=user,
            agent_id=agent.id,
            task_text="Please generate a PDF for the report",
        )

    assert suggestions == []


def test_workflow_suggestions_helper_ignores_imported_workflow_skill_from_other_owner():
    db = build_db()
    user = build_user()
    other_owner = build_user()
    agent = build_agent(user.id)
    assignment = build_imported_workflow_skill(title="PDF Generator", content="Generate PDF files from task text.")
    assignment.agent_id = agent.id
    github_import = build_github_import_record(
        import_id=assignment.skill.source_id,
        owner_id=other_owner.id,
        status="imported",
        content_preview="Workflow instruction to generate PDF files from task text.",
    )

    def fake_list_imports(_db, owner_id=None):
        if owner_id == user.id:
            return []
        return [github_import]

    with patch("app.services.skill_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.skill_service.agent_skill_repository.list_agent_skills",
        return_value=[assignment],
    ), patch(
        "app.services.skill_service.github_import_repository.list_imports",
        side_effect=fake_list_imports,
    ), patch(
        "app.services.workflow_suggestion_service.workflow_skill_binding_repository.list_bindings",
        return_value=[],
    ), patch(
        "app.services.workflow_suggestion_service.workflow_consent_repository.list_consents",
        return_value=[],
    ), patch_template_registry():
        suggestions = get_workflow_suggestions_for_agent(
            db,
            user=user,
            agent_id=agent.id,
            task_text="Please generate a PDF for the report",
        )

    assert suggestions == []


def test_workflow_suggestions_helper_ignores_imported_workflow_skill_attached_to_other_agent():
    db = build_db()
    user = build_user()
    agent = build_agent(user.id)
    other_agent = build_agent(user.id)
    assignment = build_imported_workflow_skill(title="PDF Generator", content="Generate PDF files from task text.")
    assignment.agent_id = other_agent.id
    github_import = build_github_import_record(
        import_id=assignment.skill.source_id,
        owner_id=user.id,
        status="imported",
        content_preview="Workflow instruction to generate PDF files from task text.",
    )

    with patch("app.services.skill_service.agent_repository.get_by_id", return_value=agent), patch(
        "app.services.skill_service.agent_skill_repository.list_agent_skills",
        return_value=[assignment],
    ), patch(
        "app.services.skill_service.github_import_repository.list_imports",
        return_value=[github_import],
    ), patch(
        "app.services.workflow_suggestion_service.workflow_skill_binding_repository.list_bindings",
        return_value=[],
    ), patch(
        "app.services.workflow_suggestion_service.workflow_consent_repository.list_consents",
        return_value=[],
    ), patch_template_registry():
        suggestions = get_workflow_suggestions_for_agent(
            db,
            user=user,
            agent_id=agent.id,
            task_text="Please generate a PDF for the report",
        )

    assert suggestions == []


def test_workflow_suggestions_helper_marks_missing_consent_as_unavailable():
    db = build_db()
    user = build_user()
    agent = build_agent(user.id)
    skill = build_workflow_skill(title="PDF Generator", content="Generate PDF files from task text.")
    binding = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user.id,
        skill_id=skill.skill_id,
        template_id="generate_pdf",
        template_version="1.0",
        created_at=datetime.now(UTC),
    )

    with patch("app.services.workflow_suggestion_service.skill_service.list_active_agent_skills", return_value=[skill]), patch(
        "app.services.workflow_suggestion_service.workflow_skill_binding_repository.list_bindings",
        return_value=[binding],
    ), patch(
        "app.services.workflow_suggestion_service.workflow_consent_repository.list_consents",
        return_value=[],
    ), patch_template_registry():
        suggestions = get_workflow_suggestions_for_agent(
            db,
            user=user,
            agent_id=agent.id,
            task_text="Please generate a PDF for the report",
        )

    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion.consent_required is True
    assert suggestion.binding_exists is True
    assert suggestion.execution_available is False


def test_workflow_suggestions_helper_marks_revoked_consent_as_unavailable():
    db = build_db()
    user = build_user()
    agent = build_agent(user.id)
    skill = build_workflow_skill(title="PDF Generator", content="Generate PDF files from task text.")
    binding = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user.id,
        skill_id=skill.skill_id,
        template_id="generate_pdf",
        template_version="1.0",
        created_at=datetime.now(UTC),
    )
    revoked_consent = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user.id,
        template_id="generate_pdf",
        template_version="1.0",
        consented_at=datetime.now(UTC),
        revoked_at=datetime.now(UTC),
    )

    with patch("app.services.workflow_suggestion_service.skill_service.list_active_agent_skills", return_value=[skill]), patch(
        "app.services.workflow_suggestion_service.workflow_skill_binding_repository.list_bindings",
        return_value=[binding],
    ), patch(
        "app.services.workflow_suggestion_service.workflow_consent_repository.list_consents",
        return_value=[revoked_consent],
    ), patch_template_registry():
        suggestions = get_workflow_suggestions_for_agent(
            db,
            user=user,
            agent_id=agent.id,
            task_text="Please generate a PDF for the report",
        )

    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion.consent_required is True
    assert suggestion.binding_exists is True
    assert suggestion.execution_available is False


def test_workflow_suggestions_helper_can_surface_match_without_binding_but_not_available():
    db = build_db()
    user = build_user()
    agent = build_agent(user.id)
    skill = build_workflow_skill(title="PDF Generator", content="Generate PDF files from task text.")

    with patch("app.services.workflow_suggestion_service.skill_service.list_active_agent_skills", return_value=[skill]), patch(
        "app.services.workflow_suggestion_service.workflow_skill_binding_repository.list_bindings",
        return_value=[],
    ), patch(
        "app.services.workflow_suggestion_service.workflow_consent_repository.list_consents",
        return_value=[],
    ), patch_template_registry():
        suggestions = get_workflow_suggestions_for_agent(
            db,
            user=user,
            agent_id=agent.id,
            task_text="Please generate a PDF for the report",
        )

    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion.binding_exists is False
    assert suggestion.consent_required is True
    assert suggestion.execution_available is False


def test_workflow_suggestions_helper_skips_disabled_template():
    db = build_db()
    user = build_user()
    agent = build_agent(user.id)
    skill = build_workflow_skill(title="PDF Generator", content="Generate PDF files from task text.")

    with patch("app.services.workflow_suggestion_service.skill_service.list_active_agent_skills", return_value=[skill]), patch(
        "app.services.workflow_suggestion_service.workflow_skill_binding_repository.list_bindings",
        return_value=[],
    ), patch(
        "app.services.workflow_suggestion_service.workflow_consent_repository.list_consents",
        return_value=[],
    ), patch(
        "app.services.workflow_suggestion_service.get_workflow_templates",
        return_value=[
            {
                "id": "generate_pdf",
                "name": "Generate PDF",
                "description": "Membuat file PDF dari teks",
                "input_schema": {"title": "string", "content": "string"},
                "output_type": "json",
                "enabled": False,
                "template_version": "1.0",
                "risk_level": "medium",
                "max_payload_bytes": 10000,
            }
        ],
    ), patch(
        "app.services.workflow_suggestion_service.get_workflow_template",
        return_value=build_template(enabled=False),
    ), patch(
        "app.services.workflow_suggestion_service.validate_safe_webhook_url",
        return_value=(True, None),
    ):
        suggestions = get_workflow_suggestions_for_agent(
            db,
            user=user,
            agent_id=agent.id,
            task_text="Please generate a PDF for the report",
        )

    assert suggestions == []


def test_agent_chat_includes_workflow_suggestions_without_execute_call():
    user = build_user()
    agent = build_agent(user.id)
    skill = build_workflow_skill(title="PDF Generator", content="Generate PDF files from task text.")
    setting = SimpleNamespace(preferred_provider="openai", preferred_model="gpt-4o-mini")
    api_key_record = SimpleNamespace(encrypted_api_key="encrypted")
    suggestion = WorkflowSuggestion(
        template_id="generate_pdf",
        template_name="Generate PDF",
        skill_id=str(skill.skill_id),
        skill_title="PDF Generator",
        reason="Matched workflow skill title with user task",
        consent_required=False,
        binding_exists=True,
        execution_available=True,
    )

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
        return_value=[skill],
    ), patch(
        "app.services.agent_chat_service.call_provider_chat_completion",
        return_value={"reply": "Assistant reply", "prompt_tokens": 3, "completion_tokens": 2},
    ), patch(
        "app.services.agent_chat_service.workflow_suggestion_service.get_workflow_suggestions_for_agent",
        return_value=[suggestion],
    ), patch(
        "app.services.agent_chat_service.session_service.upsert_chat_session",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ), patch(
        "app.services.agent_chat_service.log_service.record_activity",
        return_value=None,
    ), patch(
        "app.services.workflow_service.execute_workflow_template"
    ) as mock_execute:
        with SessionLocal() as db:
            response = chat_with_agent(
                db,
                owner_id=user.id,
                agent_id=agent.id,
                payload=AgentChatRequest(messages=[{"role": "user", "content": "Please generate a PDF"}]),
                current_user=user,
            )

    assert response.reply == "Assistant reply"
    assert response.workflow_suggestions and response.workflow_suggestions[0].template_id == "generate_pdf"
    mock_execute.assert_not_called()

    with SessionLocal() as db:
        executions = workflow_execution_repository.list_executions(db, user_id=user.id)
        assert executions == []


def test_orchestrator_passes_workflow_suggestions_from_agent_chat():
    user = build_user()
    agent = build_agent(user.id)
    suggestion = WorkflowSuggestion(
        template_id="generate_pdf",
        template_name="Generate PDF",
        skill_id=str(uuid.uuid4()),
        skill_title="PDF Generator",
        reason="Matched workflow skill title with user task",
        consent_required=False,
        binding_exists=True,
        execution_available=True,
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.orchestrator_service.agent_routing_service.preview_agent_routing",
        return_value=SimpleNamespace(
            task_text="Please generate a PDF",
            recommended_agent=SimpleNamespace(agent_id=agent.id, name=agent.name),
            candidate_agents=[],
            confidence="high",
            reasons=["Matched workspace task."],
            active_skill_matches=[],
            note="Preview only, no execution.",
        ),
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent",
        return_value=SimpleNamespace(
            agent_id=agent.id,
            agent_name=agent.name,
            reply="Agent reply",
            provider="openai",
            model="gpt-4o-mini",
            prompt_skills_used=["Prompt Skill"],
            knowledge_skills_used=[],
            knowledge_truncated=False,
            workflow_suggestions=[suggestion.model_dump()],
            warning=None,
        ),
    ), patch(
        "app.services.orchestrator_service.log_service.record_activity",
        return_value=None,
    ):
        response = orchestrate_workspace_chat(
            SimpleNamespace(commit=lambda: None),
            owner_id=user.id,
            payload=SimpleNamespace(session_id=None, task_text="Please generate a PDF", messages=[]),
            current_user=user,
        )

    assert response.workflow_suggestions
    assert response.workflow_suggestions[0].template_id == "generate_pdf"


def test_orchestrator_fallback_returns_empty_workflow_suggestions():
    user = build_user()

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.agent_routing_service.agent_repository.list_by_owner",
        return_value=[],
    ), patch(
        "app.services.agent_routing_service.skill_service.list_active_agent_skills",
        return_value=[],
    ), patch(
        "app.services.orchestrator_service.log_service.record_activity",
        return_value=None,
    ), patch(
        "app.services.orchestrator_service.agent_chat_service.chat_with_agent"
    ) as mock_chat:
        response = orchestrate_workspace_chat(
            SimpleNamespace(commit=lambda: None),
            owner_id=user.id,
            payload=SimpleNamespace(session_id=None, task_text="Summarize the report", messages=[]),
            current_user=user,
        )

    assert response.workflow_suggestions == []
    mock_chat.assert_not_called()
