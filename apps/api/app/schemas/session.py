from datetime import datetime
from typing import Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agent_chat import ChatMessage


class SessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_type: Literal["agent", "orchestrator"]
    agent_id: uuid.UUID | None
    agent_name: str | None = None
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int


class SessionDetail(SessionSummary):
    messages: list[ChatMessage] = Field(default_factory=list)


class SessionListResponse(BaseModel):
    sessions: list[SessionSummary] = Field(default_factory=list)


class SessionDeleteResponse(BaseModel):
    success: bool
