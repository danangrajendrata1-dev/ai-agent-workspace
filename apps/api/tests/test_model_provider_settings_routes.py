def test_model_provider_settings_requires_authentication(client):
    response = client.get("/model-provider-settings")

    assert response.status_code == 401
