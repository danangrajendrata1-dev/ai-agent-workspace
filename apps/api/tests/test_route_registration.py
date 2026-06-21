EXPECTED_PATHS = {
    "/health",
    "/auth/login",
    "/auth/me",
    "/auth/register",
    "/model-provider-keys",
    "/model-provider-keys/{provider}",
    "/model-provider-settings",
    "/model-providers",
    "/providers/test-connection",
    "/runtime/capabilities",
    "/runtime/readiness",
    "/runtime/event-contract",
    "/agents",
    "/agents/task-draft",
    "/agents/{agent_id}/chat",
    "/agents/{agent_id}/avatar",
    "/agents/{agent_id}/avatar/content",
    "/skills",
    "/skills/library",
    "/agents/routing-preview",
    "/orchestrator/chat",
    "/sessions",
    "/sessions/{session_id}",
    "/workflows/templates",
    "/workflows/consent/{template_id}",
    "/workflows/consents",
    "/workflows/consents/{consent_id}/revoke",
    "/workflows/bindings",
    "/workflows/bindings/{binding_id}",
    "/workflows/executions",
    "/workflows/executions/history",
    "/workflows/execute/{template_id}",
    "/workflows/chat-confirm-execute/{template_id}",
    "/handoff-drafts",
    "/handoff-drafts/{draft_id}",
    "/handoff-drafts/{draft_id}/archive",
    "/github-imports/skills/preview",
    "/github-imports/skills/collection-preview",
    "/github-imports/skills/import-selected",
    "/tools",
    "/memories",
    "/tasks",
    "/approvals",
    "/logs/activity",
    "/model-router/stub-test",
    "/tools/execution-stub",
    "/n8n-workflows",
    "/agents/{agent_id}/active-skills",
    "/agents/{agent_id}/skills/imported/{skill_id}",
}

EXPECTED_RUNTIME_PATHS = {
    "/runtime/capabilities",
    "/runtime/readiness",
    "/runtime/event-contract",
}


def test_openapi_schema_loads(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert "paths" in payload


def test_expected_paths_exist_in_openapi(client):
    response = client.get("/openapi.json")
    payload = response.json()
    paths = set(payload["paths"].keys())

    missing = EXPECTED_PATHS - paths
    assert not missing, f"Missing expected OpenAPI paths: {sorted(missing)}"


def test_runtime_execute_route_is_not_registered(client):
    response = client.get("/openapi.json")
    payload = response.json()
    paths = set(payload["paths"].keys())

    assert "/runtime/execute" not in paths


def test_runtime_routes_remain_read_only_get_only(client):
    response = client.get("/openapi.json")
    payload = response.json()

    runtime_paths = {path for path in payload["paths"].keys() if path.startswith("/runtime/")}
    assert runtime_paths == EXPECTED_RUNTIME_PATHS

    for path in EXPECTED_RUNTIME_PATHS:
        assert set(payload["paths"][path].keys()) == {"get"}, path
