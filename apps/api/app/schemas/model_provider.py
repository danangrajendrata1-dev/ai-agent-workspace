import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


ProviderType = Literal["api", "subscription_oauth", "local"]
AuthType = Literal["api_key", "oauth_gateway", "none"]
ProviderStatus = Literal["active", "inactive"]


class ModelProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    provider_type: ProviderType
    base_url: str | None = None
    auth_type: AuthType
    secret_reference: str | None = None
    default_model: str | None = Field(default=None, max_length=120)
    fallback_provider_id: uuid.UUID | None = None
    status: ProviderStatus = "active"
    is_private: bool = True

    @field_validator("name", "base_url", "secret_reference", "default_model", mode="before")
    @classmethod
    def strip_optional_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class ModelProviderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    provider_type: ProviderType | None = None
    base_url: str | None = None
    auth_type: AuthType | None = None
    secret_reference: str | None = None
    default_model: str | None = Field(default=None, max_length=120)
    fallback_provider_id: uuid.UUID | None = None
    status: ProviderStatus | None = None
    is_private: bool | None = None

    @field_validator("name", "base_url", "secret_reference", "default_model", mode="before")
    @classmethod
    def strip_optional_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class ModelProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    provider_type: ProviderType
    base_url: str | None
    auth_type: AuthType
    default_model: str | None
    fallback_provider_id: uuid.UUID | None
    status: ProviderStatus
    is_private: bool
    has_secret_reference: bool
    masked_secret_reference: str | None
    created_at: datetime
    updated_at: datetime


class ModelProviderListResponse(BaseModel):
    items: list[ModelProviderResponse]
