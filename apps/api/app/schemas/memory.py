import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


MemoryType = Literal[
    "profile",
    "contact",
    "project",
    "agent_instruction",
    "task_history",
    "skill",
    "sensitive_config_reference",
]
VisibilityScope = Literal["global", "agent", "private"]


class MemoryCreate(BaseModel):
    agent_id: uuid.UUID | None = None
    memory_type: MemoryType
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    visibility_scope: VisibilityScope
    metadata: dict[str, Any] | None = None

    @field_validator("title", "content", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class MemoryUpdate(BaseModel):
    agent_id: uuid.UUID | None = None
    memory_type: MemoryType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    visibility_scope: VisibilityScope | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("title", "content", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    agent_id: uuid.UUID | None
    memory_type: MemoryType
    title: str
    content: str
    visibility_scope: VisibilityScope
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class MemoryListResponse(BaseModel):
    items: list[MemoryResponse]
