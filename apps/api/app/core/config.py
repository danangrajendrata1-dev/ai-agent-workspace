from functools import lru_cache
import json
from typing import List, Literal

from pydantic import AliasChoices, Field, field_validator, model_validator
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
    agent_avatar_storage_backend: Literal["local", "gcs"] = Field(
        default="local",
        validation_alias=AliasChoices("AGENT_AVATAR_STORAGE_BACKEND"),
    )
    agent_avatar_local_dir: str = Field(
        default="var/uploads/agent-avatars",
        validation_alias=AliasChoices("AGENT_AVATAR_LOCAL_DIR"),
    )
    agent_avatar_gcs_bucket: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AGENT_AVATAR_GCS_BUCKET"),
    )
    agent_avatar_gcs_prefix: str = Field(
        default="agent-avatars",
        validation_alias=AliasChoices("AGENT_AVATAR_GCS_PREFIX"),
    )
    agent_avatar_max_bytes: int = Field(
        default=2_097_152,
        gt=0,
        validation_alias=AliasChoices("AGENT_AVATAR_MAX_BYTES"),
    )
    agent_avatar_allowed_mime_types: List[str] = Field(
        default_factory=lambda: [
            "image/png",
            "image/jpeg",
            "image/webp",
            "image/gif",
        ],
        validation_alias=AliasChoices("AGENT_AVATAR_ALLOWED_MIME_TYPES"),
    )

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

    @field_validator("agent_avatar_allowed_mime_types", mode="before")
    @classmethod
    def parse_avatar_mime_types(cls, value):
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]

        if isinstance(value, list):
            return [str(item).strip().lower() for item in value if str(item).strip()]

        return value

    @field_validator("agent_avatar_storage_backend", "agent_avatar_gcs_prefix", "agent_avatar_local_dir", mode="before")
    @classmethod
    def strip_avatar_storage_strings(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def validate_avatar_storage(self):
        if self.agent_avatar_storage_backend == "gcs" and not self.agent_avatar_gcs_bucket:
            raise ValueError("AGENT_AVATAR_GCS_BUCKET is required when AGENT_AVATAR_STORAGE_BACKEND=gcs.")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
