import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ToolType = Literal["n8n", "github", "database", "messaging", "custom"]
ToolSourceType = Literal["manual", "github", "internal", "n8n", "custom"]
ToolRiskLevel = Literal["low", "medium", "high", "critical"]
ToolStatus = Literal["active", "inactive", "disabled"]
PermissionMode = Literal["allow", "block"]


class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    slug: str | None = Field(default=None, max_length=150)
    description: str | None = None
    tool_type: ToolType
    source_type: ToolSourceType | None = None
    source_id: uuid.UUID | None = None
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    risk_level: ToolRiskLevel
    approval_required: bool = False
    timeout_seconds: int = Field(default=60, gt=0)
    rate_limit_per_hour: int | None = Field(default=None, gt=0)
    status: ToolStatus = "active"

    @field_validator("name", "slug", "description", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class ToolUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    slug: str | None = Field(default=None, max_length=150)
    description: str | None = None
    tool_type: ToolType | None = None
    source_type: ToolSourceType | None = None
    source_id: uuid.UUID | None = None
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    risk_level: ToolRiskLevel | None = None
    approval_required: bool | None = None
    timeout_seconds: int | None = Field(default=None, gt=0)
    rate_limit_per_hour: int | None = Field(default=None, gt=0)
    status: ToolStatus | None = None

    @field_validator("name", "slug", "description", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class ToolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    tool_type: ToolType
    source_type: ToolSourceType | None
    source_id: uuid.UUID | None
    input_schema: dict[str, Any] | None
    output_schema: dict[str, Any] | None
    risk_level: ToolRiskLevel
    approval_required: bool
    timeout_seconds: int
    rate_limit_per_hour: int | None
    status: ToolStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ToolListResponse(BaseModel):
    items: list[ToolResponse]


class AgentToolAssignRequest(BaseModel):
    tool_id: uuid.UUID
    is_enabled: bool = True
    permission_mode: PermissionMode
    override_approval_required: bool | None = None


class AgentToolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    tool_id: uuid.UUID
    is_enabled: bool
    permission_mode: PermissionMode
    override_approval_required: bool | None
    created_at: datetime
    tool: ToolResponse
