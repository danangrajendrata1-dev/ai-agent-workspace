import json

from app.core.config import Settings


def test_cors_origins_accepts_cloud_run_json_array(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        json.dumps(
            [
                "https://frontend.example.com/",
                "http://localhost:3000",
            ]
        ),
    )

    settings = Settings()

    assert settings.backend_cors_origins == [
        "https://frontend.example.com",
        "http://localhost:3000",
    ]


def test_cors_origins_accepts_backend_alias_json_array(monkeypatch):
    monkeypatch.setenv(
        "BACKEND_CORS_ORIGINS",
        json.dumps(
            [
                "https://frontend.example.com/",
                "http://localhost:3000/",
            ]
        ),
    )

    settings = Settings()

    assert settings.backend_cors_origins == [
        "https://frontend.example.com",
        "http://localhost:3000",
    ]
