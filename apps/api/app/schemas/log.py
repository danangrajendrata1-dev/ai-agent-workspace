import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_id: str | None
    actor_type: str
    actor_id: uuid.UUID | None
    event_type: str
    message: str
    metadata: dict | None
    created_at: datetime


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    before_data: dict | None
    after_data: dict | None
    ip_address: str | None
    created_at: datetime


class ToolCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    tool_id: uuid.UUID
    agent_id: uuid.UUID
    input_payload: dict | None
    output_payload: dict | None
    status: str
    latency_ms: int | None
    error_message: str | None
    created_at: datetime


class ModelUsageLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider_id: uuid.UUID
    agent_id: uuid.UUID | None
    task_id: uuid.UUID | None
    model_name: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    estimated_cost: Decimal | None
    latency_ms: int | None
    status: str
    error_message: str | None
    created_at: datetime


class ActivityLogListResponse(BaseModel):
    items: list[ActivityLogResponse]


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]


class ToolCallListResponse(BaseModel):
    items: list[ToolCallResponse]


class ModelUsageLogListResponse(BaseModel):
    items: list[ModelUsageLogResponse]


class LogFilterParams(BaseModel):
    request_id: str | None = None
    event_type: str | None = None
    status: str | None = None
    agent_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    tool_id: uuid.UUID | None = None
    provider_id: uuid.UUID | None = None
    limit: int = Field(default=50, ge=1, le=200)
