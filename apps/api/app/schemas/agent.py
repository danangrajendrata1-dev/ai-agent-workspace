import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


AgentStatus = Literal["active", "inactive"]
AgentAvatarInputType = Literal["emoji", "image_url", "animation_url"]
AgentAvatarStoredType = Literal["emoji", "image_url", "animation_url", "uploaded_image", "uploaded_animation"]
AgentAvatarUploadKind = Literal["uploaded_image", "uploaded_animation"]
TaskDraftConfidence = Literal["high", "medium", "low", "none"]


def _normalize_avatar_url(value: str) -> str:
    trimmed = value.strip()
    if len(trimmed) > 500:
        raise ValueError("Avatar URL must be 500 characters or fewer.")
    if trimmed.startswith("//"):
        raise ValueError("Avatar URL must include http or https scheme.")
    if trimmed.startswith("/"):
        raise ValueError("Avatar URL must be absolute.")

    from urllib.parse import urlparse

    parsed = urlparse(trimmed)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Avatar URL must use http or https.")

    return trimmed


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    description: str | None = None
    role_description: str = Field(min_length=1)
    default_model_provider_id: uuid.UUID | None = None
    default_model_name: str | None = Field(default=None, max_length=120)
    status: AgentStatus = "active"
    max_steps: int = Field(default=10, gt=0)
    max_runtime_seconds: int = Field(default=300, gt=0)
    max_token_budget: int | None = Field(default=None, gt=0)
    requires_approval_by_default: bool = False
    instruction_text: str = Field(min_length=1)
    avatar_type: AgentAvatarInputType | None = None
    avatar_value: str | None = Field(default=None, max_length=500)

    @field_validator(
        "name",
        "slug",
        "description",
        "role_description",
        "default_model_name",
        "instruction_text",
        "avatar_value",
        mode="before",
    )
    @classmethod
    def strip_optional_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def validate_avatar_fields(self):
        if self.avatar_type is None and self.avatar_value is None:
            return self

        if self.avatar_type is None or self.avatar_value is None:
            raise ValueError("avatar_type and avatar_value must be provided together.")

        if self.avatar_type == "emoji":
            if len(self.avatar_value) > 16:
                raise ValueError("Emoji avatar must be 16 characters or fewer.")
        else:
            self.avatar_value = _normalize_avatar_url(self.avatar_value)

        return self


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    description: str | None = None
    role_description: str | None = Field(default=None, min_length=1)
    default_model_provider_id: uuid.UUID | None = None
    default_model_name: str | None = Field(default=None, max_length=120)
    status: AgentStatus | None = None
    max_steps: int | None = Field(default=None, gt=0)
    max_runtime_seconds: int | None = Field(default=None, gt=0)
    max_token_budget: int | None = Field(default=None, gt=0)
    requires_approval_by_default: bool | None = None
    avatar_type: AgentAvatarInputType | None = None
    avatar_value: str | None = Field(default=None, max_length=500)

    @field_validator(
        "name",
        "slug",
        "description",
        "role_description",
        "default_model_name",
        "avatar_value",
        mode="before",
    )
    @classmethod
    def strip_optional_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def validate_avatar_fields(self):
        if self.avatar_type is None and self.avatar_value is None:
            return self

        if self.avatar_type is None or self.avatar_value is None:
            raise ValueError("avatar_type and avatar_value must be provided together.")

        if self.avatar_type == "emoji":
            if len(self.avatar_value) > 16:
                raise ValueError("Emoji avatar must be 16 characters or fewer.")
        else:
            self.avatar_value = _normalize_avatar_url(self.avatar_value)

        return self


class AgentInstructionCreate(BaseModel):
    instruction_text: str = Field(min_length=1)

    @field_validator("instruction_text", mode="before")
    @classmethod
    def strip_instruction_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class AgentInstructionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    instruction_text: str
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    role_description: str
    default_model_provider_id: uuid.UUID | None
    default_model_name: str | None
    avatar_type: AgentAvatarStoredType | None = None
    avatar_value: str | None = None
    avatar_content_url: str | None = None
    status: AgentStatus
    max_steps: int
    max_runtime_seconds: int
    max_token_budget: int | None
    requires_approval_by_default: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class AgentAvatarUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    avatar_type: AgentAvatarStoredType
    avatar_value: str
    content_type: str
    size_bytes: int
    safe_filename: str | None
    sha256: str
    avatar_content_url: str


class AgentListResponse(BaseModel):
    items: list[AgentResponse]


class AgentRoutingPreviewRequest(BaseModel):
    task_text: str = Field(min_length=1, max_length=2000)

    @field_validator("task_text", mode="before")
    @classmethod
    def strip_task_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class AgentRoutingSkillMatchResponse(BaseModel):
    skill_id: uuid.UUID
    title: str
    skill_type: str
    status: str
    security_status: str
    matched_terms: list[str] = Field(default_factory=list)
    match_score: int
    reason: str


class AgentRoutingCandidateResponse(BaseModel):
    agent_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    role_description: str | None
    score: int
    reasons: list[str] = Field(default_factory=list)
    active_skill_matches: list[AgentRoutingSkillMatchResponse] = Field(default_factory=list)


class AgentRoutingPreviewResponse(BaseModel):
    task_text: str
    recommended_agent: AgentRoutingCandidateResponse | None
    candidate_agents: list[AgentRoutingCandidateResponse] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]
    reasons: list[str] = Field(default_factory=list)
    active_skill_matches: list[AgentRoutingSkillMatchResponse] = Field(default_factory=list)
    note: str


class TaskDraftRequest(BaseModel):
    task_text: str = Field(min_length=1)

    @field_validator("task_text", mode="before")
    @classmethod
    def strip_task_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class TaskDraftSkillMatch(BaseModel):
    skill_id: str
    title: str
    skill_type: str
    relevance_note: str


class TaskDraftResponse(BaseModel):
    task_text: str
    selected_agent_id: str | None
    selected_agent_name: str | None
    confidence: TaskDraftConfidence
    reasons: list[str] = Field(default_factory=list)
    relevant_skills: list[TaskDraftSkillMatch] = Field(default_factory=list)
    task_summary: str
    safety_note: str
    status: Literal["draft_only"]
    candidate_agents: list[dict] = Field(default_factory=list)
