import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SkillSourceType = Literal["manual", "github", "template"]
SkillRiskLevel = Literal["low", "medium", "high"]
SkillStatus = Literal["active", "inactive", "disabled"]
SkillImportStatus = Literal["manual", "preview", "imported", "rejected", "disabled"]
SkillType = Literal["prompt_skill", "knowledge_skill", "tool_skill", "workflow_skill"]
SkillSecurityStatus = Literal["safe", "warning", "blocked"]


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


class SkillLibraryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    skill_type: SkillType
    source_url: str | None
    source_reference: str | None
    source_branch: str | None
    file_path: str | None
    status: SkillStatus
    import_status: SkillImportStatus
    security_status: SkillSecurityStatus
    risk_level: SkillRiskLevel
    warnings: list[str] = Field(default_factory=list)
    resource_references: list[str] = Field(default_factory=list)
    created_at: datetime
    is_attachable: bool = True
    attach_block_reason: str | None = None


class SkillLibraryListResponse(BaseModel):
    items: list[SkillLibraryItemResponse]


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
    skill: SkillLibraryItemResponse


class AgentSkillListResponse(BaseModel):
    items: list[AgentSkillResponse]
