import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


GitHubImportType = Literal["skill", "tool"]
GitHubImportStatus = Literal["preview", "imported", "rejected", "disabled"]
SkillRiskLevel = Literal["low", "medium", "high"]
SkillStatus = Literal["active", "inactive", "disabled"]


class GitHubSkillPreviewRequest(BaseModel):
    repo_url: str = Field(min_length=1)
    branch: str | None = Field(default=None, max_length=120)
    file_path: str = Field(min_length=1)

    @field_validator("repo_url", "branch", "file_path", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class GitHubImportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repo_url: str
    branch: str | None
    commit_sha: str | None
    import_type: GitHubImportType
    file_path: str
    content_preview: str | None
    status: GitHubImportStatus
    review_notes: str | None
    skill_import_type: str | None = None
    inspection_warnings: list[str] = Field(default_factory=list)
    inspection_errors: list[str] = Field(default_factory=list)
    resource_paths: list[str] = Field(default_factory=list)
    safe_resource_paths: list[str] = Field(default_factory=list)
    risky_resource_paths: list[str] = Field(default_factory=list)
    blocked_resource_paths: list[str] = Field(default_factory=list)
    has_executable_resources: bool = False
    requires_review: bool = False
    created_at: datetime
    updated_at: datetime


class GitHubImportListResponse(BaseModel):
    items: list[GitHubImportResponse]


class GitHubSkillImportApproveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    slug: str | None = Field(default=None, max_length=150)
    description: str | None = None
    version_label: str | None = Field(default=None, max_length=80)
    risk_level: SkillRiskLevel = "medium"
    status: SkillStatus = "active"
    review_notes: str | None = None

    @field_validator("name", "slug", "description", "version_label", "review_notes", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class GitHubImportRejectRequest(BaseModel):
    review_notes: str = Field(min_length=1)

    @field_validator("review_notes", mode="before")
    @classmethod
    def strip_review_notes(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value
