import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.provider_api_keys import (
    normalize_api_key,
)


ModelProviderApiKeyProvider = Literal["openai", "anthropic", "google_gemini", "openrouter", "custom"]
ModelProviderApiKeyStatus = Literal["connected", "not_connected"]


class ModelProviderApiKeySaveRequest(BaseModel):
    api_key: str = Field(min_length=1, max_length=4096)

    model_config = ConfigDict(extra="forbid")

    @field_validator("api_key", mode="before")
    @classmethod
    def strip_api_key(cls, value):
        normalized = normalize_api_key(value)
        if normalized is None:
          raise ValueError("API key is required.")
        return normalized


class ModelProviderApiKeyStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    owner_id: uuid.UUID | None = None
    provider: ModelProviderApiKeyProvider
    connection_status: ModelProviderApiKeyStatus
    masked_key: str | None = None
    key_last4: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ModelProviderApiKeyListResponse(BaseModel):
    items: list[ModelProviderApiKeyStatusResponse]


class ModelProviderApiKeyDeleteResponse(ModelProviderApiKeyStatusResponse):
    pass
