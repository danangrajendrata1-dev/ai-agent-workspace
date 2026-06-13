import os

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_NAME", "Personal AI Agent Workspace API")
os.environ.setdefault("API_VERSION", "0.1.0")
os.environ.setdefault("JWT_SECRET_KEY", "change-me-in-development")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/personal_ai_agent_workspace_test")

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def registered_paths():
    return {route.path for route in app.routes}
