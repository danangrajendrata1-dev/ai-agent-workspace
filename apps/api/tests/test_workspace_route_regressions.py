import uuid
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from app.core.security import create_access_token
from app.schemas.approval import ApprovalRequestResponse
from app.schemas.log import ActivityLogResponse, AuditLogResponse, ModelUsageLogResponse, ToolCallResponse
from app.schemas.model_provider_api_key import (
    ModelProviderApiKeyDeleteResponse,
    ModelProviderApiKeyListResponse,
    ModelProviderApiKeyStatusResponse,
)
from app.schemas.model_provider_setting import ModelProviderSettingsResponse
from app.schemas.n8n_workflow import N8nWorkflowResponse
from app.schemas.skill import AgentSkillResponse, SkillLibraryItemResponse
from app.schemas.task import TaskDetailResponse, TaskResponse, TaskStepResponse


def auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


def make_user(*, role: str = "user", plan: str = "free") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        role=role,
        subscription_plan=plan,
        is_active=True,
        deleted_at=None,
    )


def make_now() -> datetime:
    return datetime.now(UTC)


def make_task_response(user_id: uuid.UUID, task_id: uuid.UUID, *, status: str = "completed") -> TaskResponse:
    now = make_now()
    return TaskResponse(
        id=task_id,
        request_id="request-123",
        owner_id=user_id,
        agent_id=uuid.uuid4(),
        input_text="Summarize notes",
        status=status,
        selected_skill_id=None,
        selected_tool_id=None,
        final_response="Summary ready",
        error_message=None,
        started_at=now,
        completed_at=now,
        created_at=now,
        updated_at=now,
    )


def make_task_detail(user_id: uuid.UUID, task_id: uuid.UUID) -> TaskDetailResponse:
    now = make_now()
    step = TaskStepResponse(
        id=uuid.uuid4(),
        task_id=task_id,
        step_order=1,
        step_name="completed",
        status="success",
        input_summary="safe input",
        output_summary="safe output",
        error_message=None,
        created_at=now,
    )
    task_data = make_task_response(user_id, task_id).model_dump()
    task_data["steps"] = [step]
    return TaskDetailResponse.model_validate(task_data)


def make_approval_response(user_id: uuid.UUID, approval_id: uuid.UUID) -> ApprovalRequestResponse:
    now = make_now()
    return ApprovalRequestResponse(
        id=approval_id,
        task_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        tool_id=None,
        requested_action="Save workflow metadata",
        risk_level="medium",
        status="pending",
        request_payload={"reason": "workspace review"},
        decision_reason=None,
        decided_by=None,
        decided_at=None,
        created_at=now,
    )


def make_log_response() -> ActivityLogResponse:
    now = make_now()
    return ActivityLogResponse(
        id=uuid.uuid4(),
        request_id="request-123",
        actor_type="user",
        actor_id=uuid.uuid4(),
        event_type="agent.created",
        message="Agent created.",
        metadata={"source": "workspace"},
        created_at=now,
    )


def make_audit_response() -> AuditLogResponse:
    now = make_now()
    return AuditLogResponse(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        action="update",
        entity_type="agent",
        entity_id=uuid.uuid4(),
        before_data={"name": "Agent One"},
        after_data={"name": "Agent Two"},
        ip_address=None,
        created_at=now,
    )


def make_tool_call_response() -> ToolCallResponse:
    now = make_now()
    return ToolCallResponse(
        id=uuid.uuid4(),
        task_id=uuid.uuid4(),
        tool_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        input_payload={"value": "safe"},
        output_payload={"result": "ok"},
        status="blocked",
        latency_ms=25,
        error_message="Tool execution is disabled in this release.",
        created_at=now,
    )


def make_model_usage_response() -> ModelUsageLogResponse:
    now = make_now()
    return ModelUsageLogResponse(
        id=uuid.uuid4(),
        provider_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        task_id=uuid.uuid4(),
        model_name="gpt-4o-mini",
        prompt_tokens=10,
        completion_tokens=5,
        estimated_cost=Decimal("0.000000"),
        latency_ms=33,
        status="success",
        error_message=None,
        created_at=now,
    )


def make_provider_settings_response(user_id: uuid.UUID) -> ModelProviderSettingsResponse:
    now = make_now()
    return ModelProviderSettingsResponse(
        id=uuid.uuid4(),
        owner_id=user_id,
        preferred_provider="openai",
        preferred_model="gpt-4o-mini",
        connection_status="metadata_configured",
        created_at=now,
        updated_at=now,
    )


def make_provider_key_response(user_id: uuid.UUID, *, provider: str = "openai") -> ModelProviderApiKeyStatusResponse:
    now = make_now()
    return ModelProviderApiKeyStatusResponse(
        id=uuid.uuid4(),
        owner_id=user_id,
        provider=provider,
        connection_status="connected",
        masked_key="********1234",
        key_last4="1234",
        created_at=now,
        updated_at=now,
    )


def make_n8n_response(user_id: uuid.UUID, *, workflow_id: uuid.UUID | None = None) -> N8nWorkflowResponse:
    now = make_now()
    return N8nWorkflowResponse(
        id=workflow_id or uuid.uuid4(),
        owner_id=user_id,
        name="Weekly Report",
        slug="weekly-report",
        description="Workspace registry item",
        workflow_external_id="wf-001",
        trigger_type="manual",
        webhook_url_reference="workflow-webhook-ref",
        status="inactive",
        risk_level="low",
        approval_required=False,
        metadata={"agent_name": "Mail Agent"},
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


def make_skill_library_item() -> SkillLibraryItemResponse:
    now = make_now()
    return SkillLibraryItemResponse(
        id=uuid.uuid4(),
        title="Workflow Helper",
        skill_type="workflow_skill",
        source_url="https://github.com/example/repo",
        source_reference="abc1234",
        source_branch="main",
        file_path="skills/workflow/SKILL.md",
        status="active",
        import_status="imported",
        security_status="safe",
        risk_level="low",
        warnings=[],
        resource_references=["docs/guide.md"],
        created_at=now,
        is_attachable=True,
        attach_block_reason=None,
    )


def make_agent_skill_response() -> AgentSkillResponse:
    now = make_now()
    skill = make_skill_library_item()
    return AgentSkillResponse(
        id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        skill_id=skill.id,
        is_enabled=True,
        created_at=now,
        skill=skill,
    )


def test_tasks_routes_return_safe_contracts(client):
    user = make_user()
    task_id = uuid.uuid4()
    task = make_task_response(user.id, task_id)
    detail = make_task_detail(user.id, task_id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.task_service.list_tasks",
        return_value=[task],
    ), patch(
        "app.services.task_service.get_task",
        return_value=detail,
    ), patch(
        "app.services.task_service.list_agent_tasks",
        return_value=[task],
    ):
        list_response = client.get("/tasks", headers=auth_headers(user.id))
        detail_response = client.get(f"/tasks/{task_id}", headers=auth_headers(user.id))
        agent_response = client.get(f"/agents/{uuid.uuid4()}/tasks", headers=auth_headers(user.id))

    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["request_id"] == "request-123"
    assert detail_response.status_code == 200
    assert detail_response.json()["steps"][0]["step_name"] == "completed"
    assert agent_response.status_code == 200
    assert agent_response.json()["items"][0]["status"] == "completed"


def test_approval_routes_return_safe_contracts(client):
    user = make_user()
    approval_id = uuid.uuid4()
    approval = make_approval_response(user.id, approval_id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.approval_service.list_approval_requests",
        return_value=[approval],
    ), patch(
        "app.services.approval_service.list_pending_approvals",
        return_value=[approval],
    ), patch(
        "app.services.approval_service.get_approval_request",
        return_value=approval,
    ):
        list_response = client.get("/approvals", headers=auth_headers(user.id))
        pending_response = client.get("/approvals/pending", headers=auth_headers(user.id))
        detail_response = client.get(f"/approvals/{approval_id}", headers=auth_headers(user.id))

    assert list_response.status_code == 200
    assert pending_response.status_code == 200
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "pending"


def test_log_routes_return_read_only_contracts(client):
    user = make_user()
    activity = make_log_response()
    audit = make_audit_response()
    tool_call = make_tool_call_response()
    usage = make_model_usage_response()

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.log_service.list_activity_logs",
        return_value=[activity],
    ), patch(
        "app.services.log_service.get_activity_log",
        return_value=activity,
    ), patch(
        "app.services.log_service.list_audit_logs",
        return_value=[audit],
    ), patch(
        "app.services.log_service.get_audit_log",
        return_value=audit,
    ), patch(
        "app.services.log_service.list_tool_calls",
        return_value=[tool_call],
    ), patch(
        "app.services.log_service.get_tool_call",
        return_value=tool_call,
    ), patch(
        "app.services.log_service.list_model_usage_logs",
        return_value=[usage],
    ), patch(
        "app.services.log_service.get_model_usage_log",
        return_value=usage,
    ):
        activity_response = client.get("/logs/activity", headers=auth_headers(user.id))
        audit_response = client.get("/logs/audit", headers=auth_headers(user.id))
        tool_response = client.get("/logs/tool-calls", headers=auth_headers(user.id))
        usage_response = client.get("/logs/model-usage", headers=auth_headers(user.id))

    assert activity_response.status_code == 200
    assert activity_response.json()["items"][0]["event_type"] == "agent.created"
    assert audit_response.status_code == 200
    assert audit_response.json()["items"][0]["entity_type"] == "agent"
    assert tool_response.status_code == 200
    assert tool_response.json()["items"][0]["status"] == "blocked"
    assert usage_response.status_code == 200
    assert usage_response.json()["items"][0]["model_name"] == "gpt-4o-mini"


def test_model_provider_settings_routes_are_safe(client):
    user = make_user()
    current = make_provider_settings_response(user.id)
    updated = make_provider_settings_response(user.id)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.model_provider_settings_service.get_settings",
        return_value=current,
    ), patch(
        "app.services.model_provider_settings_service.update_settings",
        return_value=updated,
    ):
        get_response = client.get("/model-provider-settings", headers=auth_headers(user.id))
        patch_response = client.patch(
            "/model-provider-settings",
            headers=auth_headers(user.id),
            json={"preferred_provider": "openai", "preferred_model": "gpt-4o-mini"},
        )

    assert get_response.status_code == 200
    assert "api_key" not in get_response.text
    assert "oauth_token" not in get_response.text
    assert "refresh_token" not in get_response.text
    assert patch_response.status_code == 200
    assert patch_response.json()["preferred_provider"] == "openai"
    assert "api_key" not in patch_response.text


def test_model_provider_key_routes_return_masked_values_only(client):
    user = make_user()
    key_status = make_provider_key_response(user.id)
    key_list = ModelProviderApiKeyListResponse(items=[key_status])
    key_deleted_data = key_status.model_dump()
    key_deleted_data["connection_status"] = "not_connected"
    key_deleted_data["masked_key"] = None
    key_deleted_data["key_last4"] = None
    key_deleted = ModelProviderApiKeyDeleteResponse.model_validate(key_deleted_data)

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.model_provider_api_key_service.list_provider_api_key_statuses",
        return_value=key_list,
    ), patch(
        "app.services.model_provider_api_key_service.get_provider_api_key_status",
        return_value=key_status,
    ), patch(
        "app.services.model_provider_api_key_service.save_provider_api_key",
        return_value=key_status,
    ), patch(
        "app.services.model_provider_api_key_service.delete_provider_api_key",
        return_value=key_deleted,
    ):
        list_response = client.get("/model-provider-keys", headers=auth_headers(user.id))
        single_response = client.get("/model-provider-keys/openai", headers=auth_headers(user.id))
        save_response = client.put(
            "/model-provider-keys/openai",
            headers=auth_headers(user.id),
            json={"api_key": "sk-live-12345678"},
        )
        delete_response = client.delete("/model-provider-keys/openai", headers=auth_headers(user.id))

    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["masked_key"] == "********1234"
    assert "encrypted_api_key" not in list_response.text
    assert single_response.status_code == 200
    assert single_response.json()["connection_status"] == "connected"
    assert "api_key" not in single_response.text
    assert save_response.status_code == 200
    assert save_response.json()["masked_key"] == "********1234"
    assert delete_response.status_code == 200
    assert delete_response.json()["connection_status"] == "not_connected"


def test_n8n_route_blocks_free_plan_and_supports_registry_crud(client):
    free_user = make_user(plan="free")
    pro_user = make_user(plan="pro")
    workflow_id = uuid.uuid4()
    workflow = make_n8n_response(pro_user.id, workflow_id=workflow_id)

    with patch("app.services.auth_service.get_current_active_user", return_value=free_user), patch(
        "app.services.n8n_workflow_service.list_workflows"
    ) as mock_list_workflows:
        response = client.get("/n8n-workflows", headers=auth_headers(free_user.id))

    assert response.status_code == 403
    mock_list_workflows.assert_not_called()
    assert "Free plan" in response.text

    with patch("app.services.auth_service.get_current_active_user", return_value=pro_user), patch(
        "app.services.n8n_workflow_service.list_workflows",
        return_value=[workflow],
    ), patch(
        "app.services.n8n_workflow_service.create_workflow",
        return_value=workflow,
    ), patch(
        "app.services.n8n_workflow_service.update_workflow",
        return_value=workflow,
    ), patch(
        "app.services.n8n_workflow_service.delete_workflow",
        return_value=None,
    ):
        list_response = client.get("/n8n-workflows", headers=auth_headers(pro_user.id))
        create_response = client.post(
            "/n8n-workflows",
            headers=auth_headers(pro_user.id),
            json={
                "name": "Weekly Report",
                "trigger_type": "manual",
                "risk_level": "low",
                "approval_required": False,
            },
        )
        update_response = client.patch(
            f"/n8n-workflows/{workflow_id}",
            headers=auth_headers(pro_user.id),
            json={
                "name": "Weekly Report",
                "trigger_type": "manual",
                "risk_level": "low",
                "approval_required": False,
            },
        )
        delete_response = client.delete(f"/n8n-workflows/{workflow_id}", headers=auth_headers(pro_user.id))

    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["name"] == "Weekly Report"
    assert create_response.status_code == 201
    assert "http://" not in create_response.text
    assert update_response.status_code == 200
    assert update_response.json()["slug"] == "weekly-report"
    assert delete_response.status_code == 204


def test_skill_routes_cover_attach_detach_and_active_skills(client):
    user = make_user()
    agent_id = uuid.uuid4()
    skill_id = uuid.uuid4()
    assignment = make_agent_skill_response()

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.skill_service.attach_imported_skill_to_agent",
        return_value=assignment,
    ), patch(
        "app.services.skill_service.remove_skill_from_agent",
        return_value=None,
    ), patch(
        "app.services.skill_service.list_active_agent_skills",
        return_value=[assignment],
    ):
        attach_response = client.post(
            f"/agents/{agent_id}/skills/imported/{skill_id}",
            headers=auth_headers(user.id),
        )
        active_response = client.get(
            f"/agents/{agent_id}/active-skills",
            headers=auth_headers(user.id),
        )
        detach_response = client.delete(
            f"/agents/{agent_id}/skills/imported/{skill_id}",
            headers=auth_headers(user.id),
        )

    assert attach_response.status_code == 201
    assert attach_response.json()["skill"]["title"] == "Workflow Helper"
    assert "content" not in attach_response.text
    assert active_response.status_code == 200
    assert active_response.json()["items"][0]["skill"]["skill_type"] == "workflow_skill"
    assert detach_response.status_code == 204


def test_no_execution_routes_stay_unavailable(client):
    workflow_id = uuid.uuid4()
    import_id = uuid.uuid4()
    tool_id = uuid.uuid4()

    assert client.post(f"/n8n-workflows/{workflow_id}/execute").status_code == 404
    assert client.post(f"/n8n-workflows/{workflow_id}/activate").status_code == 404
    assert client.post(f"/github-imports/{import_id}/execute").status_code == 404
    assert client.post(f"/tools/{tool_id}/execute").status_code == 404
