import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

HandoffDraftStatus = Literal["draft", "archived"]


class HandoffDraftCreateRequest(BaseModel):
    task_text: str = Field(min_length=1, max_length=2000)
    selected_agent_id: uuid.UUID | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("task_text", mode="before")
    @classmethod
    def strip_task_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class HandoffDraftPayloadResponse(BaseModel):
    task_summary: str
    handoff_message: str
    suggested_steps: list[str] = Field(default_factory=list)
    safety_note: str


class HandoffDraftSkillMatchResponse(BaseModel):
    skill_id: uuid.UUID
    title: str
    skill_type: str
    match_reason: str


class HandoffDraftAgentResponse(BaseModel):
    agent_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    role_description: str | None


class HandoffDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    task_text: str
    routing_confidence: str | None
    routing_reasons: list[str] = Field(default_factory=list)
    recommended_agent_id: uuid.UUID | None
    selected_agent_id: uuid.UUID | None
    active_skill_matches: list[HandoffDraftSkillMatchResponse] = Field(default_factory=list)
    draft_payload: HandoffDraftPayloadResponse
    status: HandoffDraftStatus
    created_at: datetime
    updated_at: datetime
    recommended_agent: HandoffDraftAgentResponse | None = None
    selected_agent: HandoffDraftAgentResponse | None = None


class HandoffDraftListResponse(BaseModel):
    items: list[HandoffDraftResponse]
