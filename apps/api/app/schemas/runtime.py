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
RuntimeEventStatus = Literal[
    "disabled",
    "planned",
    "blocked",
    "queued_future",
    "running_future",
    "completed_future",
    "failed_future",
]
RuntimeEventType = Literal[
    "runtime_status",
    "guard_blocked",
    "future_execution_requested",
    "future_execution_completed",
    "future_execution_failed",
]
RuntimeEventConfirmationState = Literal[
    "not_required",
    "required",
    "confirmed_future",
    "denied",
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


class RuntimeEventFieldResponse(BaseModel):
    name: str
    required: bool
    description: str


class RuntimeEventContractResponse(BaseModel):
    status: Literal["disabled"]
    message: str
    event_status_values: list[RuntimeEventStatus]
    event_type_values: list[RuntimeEventType]
    confirmation_state_values: list[RuntimeEventConfirmationState]
    event_fields: list[RuntimeEventFieldResponse]
    guard_requirements: list[str]
    logging_rules: list[str]
    runtime_event_table_enabled: bool
    runtime_event_history_enabled: bool
    docs_path: str
