def test_health_returns_success(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "Personal AI Agent Workspace API"
    assert payload["version"] == "0.1.0"
    assert "request_id" in payload
