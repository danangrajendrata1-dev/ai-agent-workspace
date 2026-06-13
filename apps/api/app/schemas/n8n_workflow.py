import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


TriggerType = Literal["webhook", "manual", "scheduled"]
WorkflowStatus = Literal["active", "inactive", "disabled"]
WorkflowRiskLevel = Literal["low", "medium", "high", "critical"]


class N8nWorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    slug: str | None = Field(default=None, max_length=180)
    description: str | None = None
    workflow_external_id: str | None = Field(default=None, max_length=180)
    trigger_type: TriggerType
    webhook_url_reference: str | None = None
    status: WorkflowStatus = "inactive"
    risk_level: WorkflowRiskLevel
    approval_required: bool = True
    metadata: dict[str, Any] | None = None

    @field_validator("name", "slug", "description", "workflow_external_id", "webhook_url_reference", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class N8nWorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    slug: str | None = Field(default=None, max_length=180)
    description: str | None = None
    workflow_external_id: str | None = Field(default=None, max_length=180)
    trigger_type: TriggerType | None = None
    webhook_url_reference: str | None = None
    status: WorkflowStatus | None = None
    risk_level: WorkflowRiskLevel | None = None
    approval_required: bool | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("name", "slug", "description", "workflow_external_id", "webhook_url_reference", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class N8nWorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    workflow_external_id: str | None
    trigger_type: TriggerType
    webhook_url_reference: str | None
    status: WorkflowStatus
    risk_level: WorkflowRiskLevel
    approval_required: bool
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class N8nWorkflowListResponse(BaseModel):
    items: list[N8nWorkflowResponse]
