from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Message content cannot be empty")
        return cleaned


class AgentChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] = Field(..., min_length=1, max_length=50)


class AgentChatResponse(BaseModel):
    agent_id: str
    agent_name: str
    reply: str
    provider: str
    model: str
    prompt_skills_used: list[str]
    knowledge_skills_used: list[str]
    knowledge_truncated: bool
    warning: str | None = None
