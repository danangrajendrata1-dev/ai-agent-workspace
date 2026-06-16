from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from app.core.webhook_security import validate_safe_webhook_url


@dataclass(frozen=True, slots=True)
class WorkflowTemplateRecord:
    id: str
    name: str
    description: str
    webhook_url: str
    input_schema: dict[str, str]
    output_type: str
    enabled: bool
    template_version: str
    risk_level: str
    max_payload_bytes: int


WORKFLOW_TEMPLATES: dict[str, dict] = {
    "generate_pdf": {
        "id": "generate_pdf",
        "name": "Generate PDF",
        "description": "Membuat file PDF dari teks",
        "webhook_url": "https://example.com/webhook/generate-pdf",
        "input_schema": {
            "title": "string",
            "content": "string",
        },
        "output_type": "json",
        "enabled": False,
        "template_version": "1.0",
        "risk_level": "medium",
        "max_payload_bytes": 10000,
    }
}

_PLACEHOLDER_WEBHOOK_HOSTS = {"example.com", "www.example.com"}


def _canonical_template_record(template_id: str, template: dict) -> WorkflowTemplateRecord:
    return WorkflowTemplateRecord(
        id=str(template.get("id") or template_id),
        name=str(template.get("name") or "").strip(),
        description=str(template.get("description") or "").strip(),
        webhook_url=str(template.get("webhook_url") or "").strip(),
        input_schema=dict(template.get("input_schema") or {}),
        output_type=str(template.get("output_type") or "").strip(),
        enabled=bool(template.get("enabled", False)),
        template_version=str(template.get("template_version") or "").strip(),
        risk_level=str(template.get("risk_level") or "").strip(),
        max_payload_bytes=int(template.get("max_payload_bytes") or 0),
    )


def _is_placeholder_webhook_url(webhook_url: str) -> bool:
    lowered = webhook_url.strip().lower()
    return any(host in lowered for host in _PLACEHOLDER_WEBHOOK_HOSTS)


def get_workflow_templates(include_disabled: bool = False) -> list[dict]:
    templates: list[dict] = []
    for template_id, template in WORKFLOW_TEMPLATES.items():
        record = _canonical_template_record(template_id, template)
        if not include_disabled and not record.enabled:
            continue
        templates.append(
            {
                "id": record.id,
                "name": record.name,
                "description": record.description,
                "input_schema": deepcopy(record.input_schema),
                "output_type": record.output_type,
                "enabled": record.enabled,
                "template_version": record.template_version,
                "risk_level": record.risk_level,
                "max_payload_bytes": record.max_payload_bytes,
            }
        )
    return templates


def get_workflow_template(template_id: str) -> dict | None:
    template = WORKFLOW_TEMPLATES.get(template_id)
    if template is None:
        return None

    record = _canonical_template_record(template_id, template)
    return {
        "id": record.id,
        "name": record.name,
        "description": record.description,
        "webhook_url": record.webhook_url,
        "input_schema": deepcopy(record.input_schema),
        "output_type": record.output_type,
        "enabled": record.enabled,
        "template_version": record.template_version,
        "risk_level": record.risk_level,
        "max_payload_bytes": record.max_payload_bytes,
    }


def validate_workflow_templates() -> list[str]:
    errors: list[str] = []

    for template_id, template in WORKFLOW_TEMPLATES.items():
        record = _canonical_template_record(template_id, template)

        if not record.id:
            errors.append(f"Template '{template_id}' is missing an id.")
        if record.id != template_id:
            errors.append(f"Template '{template_id}' must use the registry key as its id.")
        if not record.name:
            errors.append(f"Template '{template_id}' is missing a name.")
        if not record.description:
            errors.append(f"Template '{template_id}' is missing a description.")
        if not record.template_version:
            errors.append(f"Template '{template_id}' is missing a template_version.")
        if record.risk_level not in {"low", "medium", "high"}:
            errors.append(f"Template '{template_id}' has an invalid risk level.")
        if not isinstance(record.input_schema, dict) or not record.input_schema:
            errors.append(f"Template '{template_id}' must define a non-empty input_schema.")
        if not isinstance(record.max_payload_bytes, int) or record.max_payload_bytes <= 0:
            errors.append(f"Template '{template_id}' must define a positive max_payload_bytes value.")
        if not isinstance(record.output_type, str) or not record.output_type.strip():
            errors.append(f"Template '{template_id}' must define an output_type.")

        if not record.webhook_url:
            errors.append(f"Template '{template_id}' is missing a webhook_url.")
            continue

        if record.enabled and _is_placeholder_webhook_url(record.webhook_url):
            errors.append(f"Template '{template_id}' cannot be enabled while using a placeholder webhook URL.")
            continue

        if record.enabled:
            is_safe, reason = validate_safe_webhook_url(record.webhook_url)
            if not is_safe:
                errors.append(f"Template '{template_id}' has an unsafe webhook URL: {reason or 'unknown reason'}.")

    return errors


WORKFLOW_TEMPLATE_VALIDATION_ERRORS = validate_workflow_templates()

if WORKFLOW_TEMPLATE_VALIDATION_ERRORS:
    raise RuntimeError(
        "Invalid workflow template registry: " + "; ".join(WORKFLOW_TEMPLATE_VALIDATION_ERRORS)
    )
