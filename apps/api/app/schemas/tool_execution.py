import uuid
from typing import Any

from pydantic import BaseModel, Field


class ToolExecutionRequest(BaseModel):
    task_id: uuid.UUID
    agent_id: uuid.UUID
    tool_id: uuid.UUID
    input_payload: dict[str, Any] | None = None


class ToolExecutionResponse(BaseModel):
    status: str
    message: str
    approval_required: bool
    approval_request_id: uuid.UUID | None
    tool_call_id: uuid.UUID | None
    execution_performed: bool
    risk_level: str
    blocked_reason: str | None = Field(default=None)
