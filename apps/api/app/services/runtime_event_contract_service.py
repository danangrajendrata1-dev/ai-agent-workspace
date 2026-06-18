from app.schemas.runtime import (
    RuntimeEventContractResponse,
    RuntimeEventFieldResponse,
)


_EVENT_STATUS_VALUES = (
    "disabled",
    "planned",
    "blocked",
    "queued_future",
    "running_future",
    "completed_future",
    "failed_future",
)

_EVENT_TYPE_VALUES = (
    "runtime_status",
    "guard_blocked",
    "future_execution_requested",
    "future_execution_completed",
    "future_execution_failed",
)

_CONFIRMATION_STATE_VALUES = (
    "not_required",
    "required",
    "confirmed_future",
    "denied",
)

_EVENT_FIELDS = (
    RuntimeEventFieldResponse(
        name="event_id",
        required=False,
        description="Future opaque event identifier for safe tracing.",
    ),
    RuntimeEventFieldResponse(
        name="agent_id",
        required=False,
        description="Future agent reference used for owner-scoped tracing.",
    ),
    RuntimeEventFieldResponse(
        name="session_id",
        required=False,
        description="Future session reference used for owner-scoped tracing.",
    ),
    RuntimeEventFieldResponse(
        name="status",
        required=True,
        description="Lifecycle status for the runtime event.",
    ),
    RuntimeEventFieldResponse(
        name="event_type",
        required=True,
        description="Safe event category for runtime readiness or guarded execution.",
    ),
    RuntimeEventFieldResponse(
        name="capability_key",
        required=False,
        description="Capability matrix key associated with the runtime event.",
    ),
    RuntimeEventFieldResponse(
        name="safe_message",
        required=False,
        description="Human-readable status message that never echoes raw prompt or provider content.",
    ),
    RuntimeEventFieldResponse(
        name="created_at",
        required=False,
        description="Timestamp for when the safe event metadata was created.",
    ),
    RuntimeEventFieldResponse(
        name="finished_at",
        required=False,
        description="Timestamp for when the safe event metadata finished.",
    ),
    RuntimeEventFieldResponse(
        name="requires_confirmation",
        required=True,
        description="Whether a future explicit confirmation is required for this event.",
    ),
    RuntimeEventFieldResponse(
        name="confirmation_state",
        required=False,
        description="Future confirmation state for guarded runtime actions.",
    ),
    RuntimeEventFieldResponse(
        name="safe_error_code",
        required=False,
        description="Safe machine-readable error code only.",
    ),
    RuntimeEventFieldResponse(
        name="safe_error_message",
        required=False,
        description="Safe human-readable error message only.",
    ),
)


def get_runtime_event_contract() -> RuntimeEventContractResponse:
    return RuntimeEventContractResponse(
        status="disabled",
        message="Runtime event contract is a safe static stub. It does not create runtime execution, events, or history.",
        event_status_values=list(_EVENT_STATUS_VALUES),
        event_type_values=list(_EVENT_TYPE_VALUES),
        confirmation_state_values=list(_CONFIRMATION_STATE_VALUES),
        event_fields=list(_EVENT_FIELDS),
        guard_requirements=[
            "Owner check",
            "Active agent check",
            "Active skill check",
            "Capability matrix visibility check only, not sole authorization",
            "Consent and confirmation where needed",
            "Provider key availability check without exposing the key",
            "No tool skill execution unless a future safety review allows it",
            "No raw model generation until a separate future checkpoint approves it",
        ],
        logging_rules=[
            "Do not log raw prompt, chat, or knowledge content into audit, activity, or history rows.",
            "Do not log raw provider responses.",
            "Do not log raw tool responses.",
            "Do not log raw webhook responses.",
            "Only safe status and event metadata may be stored for future runtime tracing.",
        ],
        runtime_event_table_enabled=False,
        runtime_event_history_enabled=False,
        docs_path="docs/agent-runtime-readiness.md",
    )
