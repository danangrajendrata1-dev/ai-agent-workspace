import os

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_NAME", "Personal AI Agent Workspace API")
os.environ.setdefault("API_VERSION", "0.1.0")
os.environ.setdefault("JWT_SECRET_KEY", "change-me-in-development")
os.environ.setdefault("PROVIDER_API_KEY_ENCRYPTION_KEY", "bRlOFWauX508GNRWzuTRqrZTXaM-gAcYCH3hUNNGw88=")

from app.main import app  # noqa: E402
from app.core.database import engine  # noqa: E402
from app.models.chat_session import ChatSession  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def ensure_chat_sessions_table():
    ChatSession.__table__.create(bind=engine, checkfirst=True)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def registered_paths():
    return {route.path for route in app.routes}
