import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ApprovalRiskLevel = Literal["low", "medium", "high", "critical"]
ApprovalStatus = Literal["pending", "approved", "rejected", "expired"]


class ApprovalRequestCreate(BaseModel):
    task_id: uuid.UUID
    agent_id: uuid.UUID
    tool_id: uuid.UUID | None = None
    requested_action: str = Field(min_length=1)
    risk_level: ApprovalRiskLevel
    request_payload: dict[str, Any] | None = None

    @field_validator("requested_action", mode="before")
    @classmethod
    def strip_requested_action(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class ApprovalDecisionRequest(BaseModel):
    decision_reason: str | None = None

    @field_validator("decision_reason", mode="before")
    @classmethod
    def strip_decision_reason(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class ApprovalRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    agent_id: uuid.UUID
    tool_id: uuid.UUID | None
    requested_action: str
    risk_level: ApprovalRiskLevel
    status: ApprovalStatus
    request_payload: dict[str, Any] | None
    decision_reason: str | None
    decided_by: uuid.UUID | None
    decided_at: datetime | None
    created_at: datetime


class ApprovalRequestListResponse(BaseModel):
    items: list[ApprovalRequestResponse]
