import re

from fastapi import HTTPException, status

from app.repositories import log_repository
from app.schemas.log import (
    ActivityLogResponse,
    AuditLogResponse,
    ModelUsageLogResponse,
    ToolCallResponse,
)


SECRET_KEY_NAMES = ("password", "token", "secret", "api_key", "authorization", "database_url")
SECRET_VALUE_PATTERNS = [
    r"(?i)^bearer\s+.+",
    r"(?i)\bsk-[A-Za-z0-9_\-]+\b",
]


def mask_sensitive_data(value):
    if isinstance(value, dict):
        masked = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(secret_key in key_text for secret_key in SECRET_KEY_NAMES):
                masked[key] = "***"
            else:
                masked[key] = mask_sensitive_data(item)
        return masked

    if isinstance(value, list):
        return [mask_sensitive_data(item) for item in value]

    if isinstance(value, str):
        if any(re.search(pattern, value) for pattern in SECRET_VALUE_PATTERNS):
            return "***"
        return value

    return value


def serialize_activity_log(log) -> ActivityLogResponse:
    return ActivityLogResponse(
        id=log.id,
        request_id=log.request_id,
        actor_type=log.actor_type,
        actor_id=log.actor_id,
        event_type=log.event_type,
        message=log.message,
        metadata=mask_sensitive_data(log.metadata_json),
        created_at=log.created_at,
    )


def serialize_audit_log(log) -> AuditLogResponse:
    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        before_data=mask_sensitive_data(log.before_data),
        after_data=mask_sensitive_data(log.after_data),
        ip_address=log.ip_address,
        created_at=log.created_at,
    )


def serialize_tool_call(log) -> ToolCallResponse:
    return ToolCallResponse(
        id=log.id,
        task_id=log.task_id,
        tool_id=log.tool_id,
        agent_id=log.agent_id,
        input_payload=mask_sensitive_data(log.input_payload),
        output_payload=mask_sensitive_data(log.output_payload),
        status=log.status,
        latency_ms=log.latency_ms,
        error_message=log.error_message,
        created_at=log.created_at,
    )


def serialize_model_usage_log(log) -> ModelUsageLogResponse:
    return ModelUsageLogResponse(
        id=log.id,
        provider_id=log.provider_id,
        agent_id=log.agent_id,
        task_id=log.task_id,
        model_name=log.model_name,
        prompt_tokens=log.prompt_tokens,
        completion_tokens=log.completion_tokens,
        estimated_cost=log.estimated_cost,
        latency_ms=log.latency_ms,
        status=log.status,
        error_message=log.error_message,
        created_at=log.created_at,
    )


def record_activity(db, **kwargs):
    kwargs["metadata_json"] = mask_sensitive_data(kwargs.get("metadata_json"))
    log = log_repository.create_activity_log(db, kwargs)
    return log


def record_audit(db, **kwargs):
    kwargs["before_data"] = mask_sensitive_data(kwargs.get("before_data"))
    kwargs["after_data"] = mask_sensitive_data(kwargs.get("after_data"))
    log = log_repository.create_audit_log(db, kwargs)
    return log


def record_tool_call(db, **kwargs):
    kwargs["input_payload"] = mask_sensitive_data(kwargs.get("input_payload"))
    kwargs["output_payload"] = mask_sensitive_data(kwargs.get("output_payload"))
    log = log_repository.create_tool_call(db, kwargs)
    return log


def record_model_usage(db, **kwargs):
    log = log_repository.create_model_usage_log(db, kwargs)
    return log


def list_activity_logs(db, **filters):
    return [serialize_activity_log(log) for log in log_repository.list_activity_logs(db, **filters)]


def list_audit_logs(db, **filters):
    return [serialize_audit_log(log) for log in log_repository.list_audit_logs(db, **filters)]


def list_tool_calls(db, *, owner_id, **filters):
    return [
        serialize_tool_call(log)
        for log in log_repository.list_tool_calls(db, owner_id=owner_id, **filters)
    ]


def list_model_usage_logs(db, *, owner_id, **filters):
    return [
        serialize_model_usage_log(log)
        for log in log_repository.list_model_usage_logs(db, owner_id=owner_id, **filters)
    ]


def get_activity_log(db, log_id):
    log = log_repository.get_activity_log(db, log_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity log not found.")
    return serialize_activity_log(log)


def get_audit_log(db, log_id):
    log = log_repository.get_audit_log(db, log_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found.")
    return serialize_audit_log(log)


def get_tool_call(db, *, owner_id, log_id):
    log = log_repository.get_tool_call(db, owner_id=owner_id, tool_call_id=log_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool call log not found.")
    return serialize_tool_call(log)


def get_model_usage_log(db, *, owner_id, log_id):
    log = log_repository.get_model_usage_log(db, owner_id=owner_id, usage_log_id=log_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model usage log not found.")
    return serialize_model_usage_log(log)
