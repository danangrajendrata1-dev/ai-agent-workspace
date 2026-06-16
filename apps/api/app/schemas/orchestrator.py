from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.agent_chat import ChatMessage


class OrchestratorRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_text: str = Field(..., min_length=1, max_length=4000)
    messages: list[ChatMessage] = Field(default_factory=list, max_length=50)

    @field_validator("task_text")
    @classmethod
    def validate_task_text(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Task text cannot be empty")
        return cleaned


class OrchestratorResponse(BaseModel):
    task_text: str
    routed_to_agent_id: str | None
    routed_to_agent_name: str | None
    confidence: Literal["high", "medium", "low", "none"]
    reply: str
    provider: str | None = None
    model: str | None = None
    prompt_skills_used: list[str] = Field(default_factory=list)
    knowledge_skills_used: list[str] = Field(default_factory=list)
    knowledge_truncated: bool = False
    routing_reasons: list[str] = Field(default_factory=list)
    status: Literal["routed", "fallback"]
    warning: str | None = None
