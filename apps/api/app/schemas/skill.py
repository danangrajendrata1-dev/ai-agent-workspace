import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SkillSourceType = Literal["manual", "github", "template"]
SkillRiskLevel = Literal["low", "medium", "high"]
SkillStatus = Literal["active", "inactive", "disabled"]


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    slug: str | None = Field(default=None, max_length=150)
    description: str | None = None
    content: str = Field(min_length=1)
    source_type: SkillSourceType = "manual"
    source_id: uuid.UUID | None = None
    version_label: str | None = Field(default=None, max_length=80)
    risk_level: SkillRiskLevel
    status: SkillStatus = "active"

    @field_validator(
        "name",
        "slug",
        "description",
        "content",
        "version_label",
        mode="before",
    )
    @classmethod
    def strip_optional_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class SkillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    slug: str | None = Field(default=None, max_length=150)
    description: str | None = None
    content: str | None = Field(default=None, min_length=1)
    source_type: SkillSourceType | None = None
    source_id: uuid.UUID | None = None
    version_label: str | None = Field(default=None, max_length=80)
    risk_level: SkillRiskLevel | None = None
    status: SkillStatus | None = None

    @field_validator(
        "name",
        "slug",
        "description",
        "content",
        "version_label",
        mode="before",
    )
    @classmethod
    def strip_optional_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    content: str
    source_type: SkillSourceType
    source_id: uuid.UUID | None
    version_label: str | None
    risk_level: SkillRiskLevel
    status: SkillStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class SkillListResponse(BaseModel):
    items: list[SkillResponse]


class AgentSkillAssignRequest(BaseModel):
    skill_id: uuid.UUID
    is_enabled: bool = True


class AgentSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    skill_id: uuid.UUID
    is_enabled: bool
    created_at: datetime
    skill: SkillResponse
