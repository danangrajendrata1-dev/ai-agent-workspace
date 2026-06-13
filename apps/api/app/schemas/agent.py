import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


AgentStatus = Literal["active", "inactive"]


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    description: str | None = None
    role_description: str = Field(min_length=1)
    default_model_provider_id: uuid.UUID | None = None
    default_model_name: str | None = Field(default=None, max_length=120)
    status: AgentStatus = "active"
    max_steps: int = Field(default=10, gt=0)
    max_runtime_seconds: int = Field(default=300, gt=0)
    max_token_budget: int | None = Field(default=None, gt=0)
    requires_approval_by_default: bool = False
    instruction_text: str = Field(min_length=1)

    @field_validator(
        "name",
        "slug",
        "description",
        "role_description",
        "default_model_name",
        "instruction_text",
        mode="before",
    )
    @classmethod
    def strip_optional_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    description: str | None = None
    role_description: str | None = Field(default=None, min_length=1)
    default_model_provider_id: uuid.UUID | None = None
    default_model_name: str | None = Field(default=None, max_length=120)
    status: AgentStatus | None = None
    max_steps: int | None = Field(default=None, gt=0)
    max_runtime_seconds: int | None = Field(default=None, gt=0)
    max_token_budget: int | None = Field(default=None, gt=0)
    requires_approval_by_default: bool | None = None

    @field_validator(
        "name",
        "slug",
        "description",
        "role_description",
        "default_model_name",
        mode="before",
    )
    @classmethod
    def strip_optional_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class AgentInstructionCreate(BaseModel):
    instruction_text: str = Field(min_length=1)

    @field_validator("instruction_text", mode="before")
    @classmethod
    def strip_instruction_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class AgentInstructionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    instruction_text: str
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    role_description: str
    default_model_provider_id: uuid.UUID | None
    default_model_name: str | None
    status: AgentStatus
    max_steps: int
    max_runtime_seconds: int
    max_token_budget: int | None
    requires_approval_by_default: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class AgentListResponse(BaseModel):
    items: list[AgentResponse]
