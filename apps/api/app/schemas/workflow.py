from datetime import datetime
from typing import Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field


class WorkflowTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    input_schema: dict[str, str] = Field(default_factory=dict)
    template_version: str
    risk_level: str
    output_type: str
    enabled: bool
    max_payload_bytes: int
    consented: bool = False
    consented_at: datetime | None = None


class WorkflowTemplateListResponse(BaseModel):
    items: list[WorkflowTemplateResponse]


class WorkflowConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    template_id: str
    template_name: str
    template_version: str
    consented_at: datetime
    revoked_at: datetime | None = None
    status: Literal["active", "revoked"]


class WorkflowConsentListResponse(BaseModel):
    items: list[WorkflowConsentResponse]


class WorkflowSkillBindingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_id: str = Field(min_length=1)
    template_id: str = Field(min_length=1)


class WorkflowSkillBindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str
    skill_type: str
    template_id: str
    template_name: str
    template_version: str
    created_at: datetime


class WorkflowSkillBindingListResponse(BaseModel):
    items: list[WorkflowSkillBindingResponse]


class WorkflowExecutionSummary(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    agent_id: uuid.UUID | None
    skill_id: uuid.UUID | None
    template_id: str
    template_name: str
    template_version: str
    consent_id: uuid.UUID | None
    status: str
    error_message: str | None
    http_status_code: int | None
    output_summary: str | None
    executed_at: datetime


class WorkflowExecutionListResponse(BaseModel):
    items: list[WorkflowExecutionSummary]


class WorkflowExecutionHistoryItem(BaseModel):
    id: uuid.UUID
    template_id: str
    template_name: str
    template_version: str
    agent_id: uuid.UUID | None
    skill_id: uuid.UUID | None
    status: str
    error_message: str | None
    http_status_code: int | None
    created_at: datetime
    completed_at: datetime | None = None


class WorkflowExecutionHistoryListResponse(BaseModel):
    items: list[WorkflowExecutionHistoryItem]


class WorkflowExecutionRequest(BaseModel):
    agent_id: str = Field(min_length=1)
    skill_id: str = Field(min_length=1)
    input_payload: dict = Field(default_factory=dict)


class WorkflowChatExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(min_length=1)
    skill_id: str = Field(min_length=1)
    input_payload: dict = Field(default_factory=dict)
    confirmed: bool = Field(default=True)
    confirmation_source: Literal["chat_suggestion"] = "chat_suggestion"


class WorkflowExecutionResponse(BaseModel):
    success: bool
    status: Literal["success", "failed", "timeout", "consent_required"]
    template_id: str
    template_version: str
    execution_id: str | None = None
    output_summary: str | None = None
    error_message: str | None = None
    http_status_code: int | None = None
