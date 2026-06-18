from typing import Literal

from pydantic import BaseModel


RuntimeCapabilityStatus = Literal["disabled", "suggestion_only", "explicit_confirm", "forbidden"]
RuntimeReadinessStatus = Literal[
    "disabled",
    "planned",
    "queued_future",
    "blocked",
    "completed_future",
    "failed_future",
]


class RuntimeCapabilityResponse(BaseModel):
    key: str
    status: RuntimeCapabilityStatus
    label: str
    description: str
    requires_confirmation: bool
    user_visible: bool


class RuntimeCapabilityListResponse(BaseModel):
    items: list[RuntimeCapabilityResponse]


class RuntimeReadinessResponse(BaseModel):
    status: RuntimeReadinessStatus
    message: str
    runtime_execution_enabled: bool
    tool_execution_enabled: bool
    model_raw_generation_enabled: bool
    requires_future_safety_review: bool
    docs_path: str
