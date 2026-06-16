from functools import lru_cache
import json
from typing import List

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Personal AI Agent Workspace API"
    app_env: str = "development"
    api_version: str = "0.1.0"
    backend_cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        validation_alias=AliasChoices("BACKEND_CORS_ORIGINS", "CORS_ORIGINS"),
    )
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/"
        "personal_ai_agent_workspace"
    )
    jwt_secret_key: str = "change-me-in-development"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    provider_api_key_encryption_key: str | None = None
    chat_session_encryption_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []

            if stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                except json.JSONDecodeError:
                    parsed = stripped
            else:
                parsed = stripped

            if isinstance(parsed, list):
                return [str(origin).strip().rstrip("/") for origin in parsed if str(origin).strip()]

            return [origin.strip().rstrip("/") for origin in str(parsed).split(",") if origin.strip()]

        if isinstance(value, list):
            return [str(origin).strip().rstrip("/") for origin in value if str(origin).strip()]

        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
