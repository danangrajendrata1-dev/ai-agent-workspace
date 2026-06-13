import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


TaskStatus = Literal[
    "received",
    "thinking",
    "loading_memory",
    "selecting_skill",
    "selecting_tool",
    "waiting_approval",
    "running_tool",
    "completed",
    "failed",
    "cancelled",
]
TaskStepStatus = Literal["success", "failed", "running", "skipped"]


class AgentChatRequest(BaseModel):
    input_text: str = Field(min_length=1)
    request_id: str | None = Field(default=None, max_length=120)

    @field_validator("input_text", "request_id", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class TaskStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    step_order: int
    step_name: str
    status: TaskStepStatus
    input_summary: str | None
    output_summary: str | None
    error_message: str | None
    created_at: datetime


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_id: str
    owner_id: uuid.UUID
    agent_id: uuid.UUID
    input_text: str
    status: TaskStatus
    selected_skill_id: uuid.UUID | None
    selected_tool_id: uuid.UUID | None
    final_response: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskDetailResponse(TaskResponse):
    steps: list[TaskStepResponse]


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
