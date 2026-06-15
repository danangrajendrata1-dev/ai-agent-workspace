import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.provider_settings import (
    MAX_PREFERRED_MODEL_LENGTH,
    looks_secret_like,
    normalize_optional_text,
)


ModelProviderId = Literal[
    "openai",
    "anthropic",
    "google_gemini",
    "openrouter",
    "ollama_local",
    "custom",
]
ConnectionStatus = Literal["not_connected", "metadata_configured"]


class ModelProviderSettingsUpdate(BaseModel):
    preferred_provider: ModelProviderId | None = None
    preferred_model: str | None = Field(default=None, max_length=MAX_PREFERRED_MODEL_LENGTH)

    model_config = ConfigDict(extra="forbid")

    @field_validator("preferred_model", mode="before")
    @classmethod
    def strip_preferred_model(cls, value):
        return normalize_optional_text(value)

    @field_validator("preferred_model")
    @classmethod
    def reject_secret_like_model(cls, value):
        if value and looks_secret_like(value):
            raise ValueError("Preferred model must not look like a secret or credential.")
        return value


class ModelProviderSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    preferred_provider: ModelProviderId | None
    preferred_model: str | None
    connection_status: ConnectionStatus
    created_at: datetime
    updated_at: datetime
