from __future__ import annotations

from app.schemas.runtime import RuntimeCapabilityResponse


_RUNTIME_CAPABILITIES: tuple[dict, ...] = (
    {
        "key": "chat.agent_message",
        "status": "explicit_confirm",
        "label": "Agent chat message",
        "description": "User-initiated chat request to the model; never auto-runs.",
        "requires_confirmation": True,
        "user_visible": True,
    },
    {
        "key": "chat.workflow_suggestion",
        "status": "suggestion_only",
        "label": "Workflow suggestion",
        "description": "Workflow matches may be suggested, but they never execute automatically.",
        "requires_confirmation": False,
        "user_visible": True,
    },
    {
        "key": "workflow.explicit_execute",
        "status": "explicit_confirm",
        "label": "Explicit workflow execute",
        "description": "Workflow runs only after a direct user execution action.",
        "requires_confirmation": True,
        "user_visible": True,
    },
    {
        "key": "workflow.chat_confirm_execute",
        "status": "explicit_confirm",
        "label": "Chat-confirm workflow execute",
        "description": "Workflow runs only after an explicit per-run confirmation from chat.",
        "requires_confirmation": True,
        "user_visible": True,
    },
    {
        "key": "workflow.execution_history",
        "status": "disabled",
        "label": "Workflow execution history",
        "description": "Read-only execution visibility only; no runtime action is performed.",
        "requires_confirmation": False,
        "user_visible": True,
    },
    {
        "key": "workflow.consent_revoke",
        "status": "explicit_confirm",
        "label": "Workflow consent revoke",
        "description": "Revocation requires an explicit user click and only removes future consent.",
        "requires_confirmation": True,
        "user_visible": True,
    },
    {
        "key": "tool.execution",
        "status": "forbidden",
        "label": "Tool execution",
        "description": "Direct tool runtime execution remains blocked in this release.",
        "requires_confirmation": False,
        "user_visible": True,
    },
    {
        "key": "tool_skill.execution",
        "status": "forbidden",
        "label": "Tool skill execution",
        "description": "Tool skill runtime execution is not available in this release.",
        "requires_confirmation": False,
        "user_visible": True,
    },
    {
        "key": "model_provider.connection_test",
        "status": "explicit_confirm",
        "label": "Model provider connection test",
        "description": "Connection test is only run when a user explicitly triggers it.",
        "requires_confirmation": True,
        "user_visible": True,
    },
    {
        "key": "model_provider.raw_generation",
        "status": "explicit_confirm",
        "label": "Model provider generation",
        "description": "Model generation is only triggered by an explicit user request.",
        "requires_confirmation": True,
        "user_visible": True,
    },
    {
        "key": "oauth.connection",
        "status": "forbidden",
        "label": "OAuth connection",
        "description": "OAuth connection flows are not enabled in this release.",
        "requires_confirmation": False,
        "user_visible": True,
    },
    {
        "key": "payment.billing",
        "status": "forbidden",
        "label": "Payment billing",
        "description": "Billing runtime features are not enabled in this release.",
        "requires_confirmation": False,
        "user_visible": True,
    },
    {
        "key": "custom_webhook.execution",
        "status": "forbidden",
        "label": "Custom webhook execution",
        "description": "User-supplied webhook execution is blocked by design.",
        "requires_confirmation": False,
        "user_visible": True,
    },
    {
        "key": "user_supplied_webhook.execution",
        "status": "forbidden",
        "label": "User-supplied webhook execution",
        "description": "Free-form webhook execution is blocked by design.",
        "requires_confirmation": False,
        "user_visible": True,
    },
)


def list_runtime_capabilities() -> list[RuntimeCapabilityResponse]:
    return [
        RuntimeCapabilityResponse.model_validate(capability)
        for capability in _RUNTIME_CAPABILITIES
        if capability.get("user_visible")
    ]
