EXPECTED_PATHS = {
    "/health",
    "/auth/login",
    "/auth/me",
    "/auth/register",
    "/model-providers",
    "/agents",
    "/skills",
    "/github-imports/skills/preview",
    "/tools",
    "/memories",
    "/tasks",
    "/approvals",
    "/logs/activity",
    "/model-router/stub-test",
    "/tools/execution-stub",
    "/n8n-workflows",
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
