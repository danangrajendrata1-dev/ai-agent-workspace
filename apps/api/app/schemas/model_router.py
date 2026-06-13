import uuid

from pydantic import BaseModel, Field, field_validator


class ModelRouterRequest(BaseModel):
    provider_id: uuid.UUID
    agent_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    model_name: str | None = Field(default=None, max_length=120)
    prompt: str = Field(min_length=1)

    @field_validator("model_name", "prompt", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class ModelRouterResponse(BaseModel):
    provider_id: uuid.UUID
    provider_type: str
    model_name: str | None
    output_text: str
    stub: bool
    latency_ms: int
