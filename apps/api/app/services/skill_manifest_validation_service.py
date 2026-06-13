from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import re
from typing import Any


_ALLOWED_TOP_LEVEL_FIELDS = {
    "name",
    "version",
    "description",
    "author",
    "required_capabilities",
    "required_tools",
    "required_credentials",
    "required_domains",
    "n8n_workflow",
    "permissions_requested",
    "safety_notes",
}

_REQUIRED_STRING_FIELDS = {
    "name": 120,
    "version": 40,
    "description": 1000,
}

_OPTIONAL_STRING_FIELDS = {
    "author": 120,
    "safety_notes": 2000,
}

_OPTIONAL_STRING_LIST_FIELDS = {
    "required_capabilities": 50,
    "required_tools": 50,
    "permissions_requested": 100,
}

_ALLOWED_CREDENTIAL_FIELDS = {
    "type",
    "label",
    "reason",
    "required",
}

_FORBIDDEN_CREDENTIAL_FIELDS = {
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "client_secret",
    "private_key",
    "credential",
    "value",
    "oauth_token",
}

_ALLOWED_N8N_FIELDS = {
    "template_name",
    "template_version",
    "description",
    "required_nodes",
    "risk_level",
}

_FORBIDDEN_NESTED_KEYS = {
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "client_secret",
    "private_key",
    "credential_value",
    "oauth_token",
    ".env",
    "code",
    "script",
    "nodes",
    "connections",
    "credentials",
    "active",
    "execute",
    "webhook",
}

_FORBIDDEN_EXECUTION_TOKENS = {
    "exec",
    "eval",
    "subprocess",
    "shell",
    "cmd",
    "powershell",
    "bash",
    "curl",
    "wget",
    "npm install",
    "pip install",
    "docker run",
    "n8n execute",
    "hermes",
    "openclaw",
}

_DOMAIN_LABEL_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_DOMAIN_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")
_EXECUTION_WORD_PATTERNS = [
    re.compile(r"\bexec\b", re.IGNORECASE),
    re.compile(r"\beval\b", re.IGNORECASE),
    re.compile(r"\bsubprocess\b", re.IGNORECASE),
    re.compile(r"\bshell\b", re.IGNORECASE),
    re.compile(r"\bcmd\b", re.IGNORECASE),
    re.compile(r"\bpowershell\b", re.IGNORECASE),
    re.compile(r"\bbash\b", re.IGNORECASE),
    re.compile(r"\bcurl\b", re.IGNORECASE),
    re.compile(r"\bwget\b", re.IGNORECASE),
    re.compile(r"\bn8n execute\b", re.IGNORECASE),
    re.compile(r"\bhermes\b", re.IGNORECASE),
    re.compile(r"\bopenclaw\b", re.IGNORECASE),
]


@dataclass(slots=True)
class SkillManifestValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    normalized_manifest: dict[str, Any] | None


def validate_skill_manifest(manifest: dict[str, Any]) -> SkillManifestValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(manifest, dict):
        return SkillManifestValidationResult(
            is_valid=False,
            errors=["Manifest must be a dictionary."],
            warnings=warnings,
            normalized_manifest=None,
        )

    normalized_manifest: dict[str, Any] = {
        "name": None,
        "version": None,
        "description": None,
        "author": None,
        "required_capabilities": [],
        "required_tools": [],
        "required_credentials": [],
        "required_domains": [],
        "n8n_workflow": None,
        "permissions_requested": [],
        "safety_notes": None,
    }

    _validate_top_level_keys(manifest, errors)
    _validate_required_string_fields(manifest, normalized_manifest, errors)
    _validate_optional_string_fields(manifest, normalized_manifest, errors)
    _validate_string_lists(manifest, normalized_manifest, errors)
    _validate_required_credentials(manifest, normalized_manifest, errors)
    _validate_required_domains(manifest, normalized_manifest, errors)
    _validate_n8n_workflow(manifest, normalized_manifest, errors)
    _scan_forbidden_content(manifest, errors)

    if errors:
        return SkillManifestValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            normalized_manifest=None,
        )

    return SkillManifestValidationResult(
        is_valid=True,
        errors=errors,
        warnings=warnings,
        normalized_manifest=normalized_manifest,
    )


def _validate_top_level_keys(manifest: dict[str, Any], errors: list[str]) -> None:
    for key in manifest.keys():
        if not isinstance(key, str):
            errors.append("Top-level field names must be strings.")
            continue
        if key not in _ALLOWED_TOP_LEVEL_FIELDS:
            errors.append(f"Unknown top-level field: {key}.")


def _validate_required_string_fields(
    manifest: dict[str, Any],
    normalized_manifest: dict[str, Any],
    errors: list[str],
) -> None:
    for field_name, max_length in _REQUIRED_STRING_FIELDS.items():
        value = manifest.get(field_name)
        if not isinstance(value, str):
            errors.append(f"Field '{field_name}' is required and must be a string.")
            continue

        stripped = value.strip()
        if not stripped:
            errors.append(f"Field '{field_name}' is required and must not be empty.")
            continue
        if len(stripped) > max_length:
            errors.append(f"Field '{field_name}' must not exceed {max_length} characters.")
            continue

        normalized_manifest[field_name] = stripped


def _validate_optional_string_fields(
    manifest: dict[str, Any],
    normalized_manifest: dict[str, Any],
    errors: list[str],
) -> None:
    for field_name, max_length in _OPTIONAL_STRING_FIELDS.items():
        if field_name not in manifest:
            continue

        value = manifest.get(field_name)
        if value is None:
            errors.append(f"Field '{field_name}' must be a string if provided.")
            continue
        if not isinstance(value, str):
            errors.append(f"Field '{field_name}' must be a string if provided.")
            continue

        stripped = value.strip()
        if not stripped:
            normalized_manifest[field_name] = None
            continue
        if len(stripped) > max_length:
            errors.append(f"Field '{field_name}' must not exceed {max_length} characters.")
            continue

        normalized_manifest[field_name] = stripped


def _validate_string_lists(
    manifest: dict[str, Any],
    normalized_manifest: dict[str, Any],
    errors: list[str],
) -> None:
    for field_name, max_items in _OPTIONAL_STRING_LIST_FIELDS.items():
        if field_name not in manifest:
            continue

        value = manifest.get(field_name)
        if value is None:
            errors.append(f"Field '{field_name}' must be a list if provided.")
            continue
        if not isinstance(value, list):
            errors.append(f"Field '{field_name}' must be a list if provided.")
            continue
        if len(value) > max_items:
            errors.append(f"Field '{field_name}' must not contain more than {max_items} items.")
            continue

        normalized_items: list[str] = []
        for index, item in enumerate(value):
            if not isinstance(item, str):
                errors.append(f"Field '{field_name}' item {index} must be a string.")
                continue
            stripped = item.strip()
            if not stripped:
                errors.append(f"Field '{field_name}' item {index} must not be empty.")
                continue
            normalized_items.append(stripped)

        normalized_manifest[field_name] = normalized_items


def _validate_required_credentials(
    manifest: dict[str, Any],
    normalized_manifest: dict[str, Any],
    errors: list[str],
) -> None:
    if "required_credentials" not in manifest:
        return

    value = manifest.get("required_credentials")
    if value is None:
        errors.append("Field 'required_credentials' must be a list if provided.")
        return
    if not isinstance(value, list):
        errors.append("Field 'required_credentials' must be a list if provided.")
        return
    if len(value) > 50:
        errors.append("Field 'required_credentials' must not contain more than 50 items.")
        return

    normalized_items: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"Field 'required_credentials' item {index} must be an object.")
            continue

        if any(not isinstance(key, str) for key in item.keys()):
            errors.append(f"Field 'required_credentials' item {index} must use string field names only.")
            continue

        item_keys = {str(key).lower() for key in item.keys() if isinstance(key, str)}
        forbidden_keys = sorted(item_keys & _FORBIDDEN_CREDENTIAL_FIELDS)
        if forbidden_keys:
            errors.append(
                f"Field 'required_credentials' item {index} contains forbidden field(s): {', '.join(forbidden_keys)}."
            )
            continue

        unknown_keys = sorted(key for key in item_keys if key not in _ALLOWED_CREDENTIAL_FIELDS)
        if unknown_keys:
            errors.append(
                f"Field 'required_credentials' item {index} contains unknown field(s): {', '.join(unknown_keys)}."
            )
            continue

        credential_type = item.get("type")
        if not isinstance(credential_type, str):
            errors.append(f"Field 'required_credentials' item {index} must include a string 'type'.")
            continue

        credential_type = credential_type.strip()
        if not credential_type:
            errors.append(f"Field 'required_credentials' item {index} must include a non-empty 'type'.")
            continue
        if len(credential_type) > 80:
            errors.append(f"Field 'required_credentials' item {index} 'type' must not exceed 80 characters.")
            continue

        label = item.get("label")
        if "label" in item:
            if label is None:
                errors.append(f"Field 'required_credentials' item {index} 'label' must be a string if provided.")
                continue
            if not isinstance(label, str):
                errors.append(f"Field 'required_credentials' item {index} 'label' must be a string.")
                continue
            label = label.strip() or None
            if label is not None and len(label) > 120:
                errors.append(f"Field 'required_credentials' item {index} 'label' must not exceed 120 characters.")
                continue

        reason = item.get("reason")
        if "reason" in item:
            if reason is None:
                errors.append(f"Field 'required_credentials' item {index} 'reason' must be a string if provided.")
                continue
            if not isinstance(reason, str):
                errors.append(f"Field 'required_credentials' item {index} 'reason' must be a string.")
                continue
            reason = reason.strip() or None
            if reason is not None and len(reason) > 500:
                errors.append(f"Field 'required_credentials' item {index} 'reason' must not exceed 500 characters.")
                continue

        required = item.get("required", False)
        if not isinstance(required, bool):
            errors.append(f"Field 'required_credentials' item {index} 'required' must be a boolean if provided.")
            continue

        normalized_item = {
            "type": credential_type,
            "label": label,
            "reason": reason,
            "required": required,
        }
        normalized_items.append(normalized_item)

    normalized_manifest["required_credentials"] = normalized_items


def _validate_required_domains(
    manifest: dict[str, Any],
    normalized_manifest: dict[str, Any],
    errors: list[str],
) -> None:
    if "required_domains" not in manifest:
        return

    value = manifest.get("required_domains")
    if value is None:
        errors.append("Field 'required_domains' must be a list if provided.")
        return
    if not isinstance(value, list):
        errors.append("Field 'required_domains' must be a list if provided.")
        return
    if len(value) > 100:
        errors.append("Field 'required_domains' must not contain more than 100 items.")
        return

    normalized_items: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(f"Field 'required_domains' item {index} must be a string.")
            continue
        normalized_domain, domain_error = _normalize_and_validate_domain(item)
        if domain_error is not None:
            errors.append(f"Field 'required_domains' item {index} {domain_error}")
            continue
        normalized_items.append(normalized_domain)

    normalized_manifest["required_domains"] = normalized_items


def _validate_n8n_workflow(
    manifest: dict[str, Any],
    normalized_manifest: dict[str, Any],
    errors: list[str],
) -> None:
    if "n8n_workflow" not in manifest:
        return

    value = manifest.get("n8n_workflow")
    if value is None:
        errors.append("Field 'n8n_workflow' must be an object if provided.")
        return
    if not isinstance(value, dict):
        errors.append("Field 'n8n_workflow' must be an object if provided.")
        return

    workflow_keys = {str(key).lower() for key in value.keys() if isinstance(key, str)}
    if any(not isinstance(key, str) for key in value.keys()):
        errors.append("Field 'n8n_workflow' must use string field names only.")
        return
    forbidden_keys = sorted(workflow_keys & {"nodes", "connections", "credentials", "active", "execute", "webhook", "code", "script"})
    if forbidden_keys:
        errors.append(f"Field 'n8n_workflow' contains forbidden field(s): {', '.join(forbidden_keys)}.")
        return

    unknown_keys = sorted(key for key in workflow_keys if key not in _ALLOWED_N8N_FIELDS)
    if unknown_keys:
        errors.append(f"Field 'n8n_workflow' contains unknown field(s): {', '.join(unknown_keys)}.")
        return

    normalized_workflow: dict[str, Any] = {
        "template_name": None,
        "template_version": None,
        "description": None,
        "required_nodes": [],
        "risk_level": None,
    }

    for field_name, max_length in (
        ("template_name", 120),
        ("template_version", 40),
        ("description", 1000),
        ("risk_level", 40),
    ):
        if field_name not in value:
            continue
        field_value = value.get(field_name)
        if field_value is None:
            errors.append(f"Field 'n8n_workflow.{field_name}' must be a string if provided.")
            continue
        if not isinstance(field_value, str):
            errors.append(f"Field 'n8n_workflow.{field_name}' must be a string if provided.")
            continue
        stripped = field_value.strip()
        if not stripped:
            normalized_workflow[field_name] = None
            continue
        if len(stripped) > max_length:
            errors.append(
                f"Field 'n8n_workflow.{field_name}' must not exceed {max_length} characters."
            )
            continue
        normalized_workflow[field_name] = stripped

    if "required_nodes" in value:
        required_nodes = value.get("required_nodes")
        if required_nodes is None:
            errors.append("Field 'n8n_workflow.required_nodes' must be a list if provided.")
        elif not isinstance(required_nodes, list):
            errors.append("Field 'n8n_workflow.required_nodes' must be a list if provided.")
        elif len(required_nodes) > 50:
            errors.append("Field 'n8n_workflow.required_nodes' must not contain more than 50 items.")
        else:
            normalized_nodes: list[str] = []
            for index, item in enumerate(required_nodes):
                if not isinstance(item, str):
                    errors.append(f"Field 'n8n_workflow.required_nodes' item {index} must be a string.")
                    continue
                stripped = item.strip()
                if not stripped:
                    errors.append(f"Field 'n8n_workflow.required_nodes' item {index} must not be empty.")
                    continue
                normalized_nodes.append(stripped)
            normalized_workflow["required_nodes"] = normalized_nodes

    normalized_manifest["n8n_workflow"] = normalized_workflow


def _normalize_and_validate_domain(value: str) -> tuple[str, str | None]:
    domain = value.strip().lower()
    if not domain:
        return domain, "must not be empty."
    if len(domain) > 253:
        return domain, "must not exceed 253 characters."
    if any(separator in domain for separator in ("://", "/", "?", "#", "@")):
        return domain, "must not include a protocol, path, query, or userinfo."
    if ":" in domain:
        return domain, "must not include a port or IPv6 notation."
    if "*" in domain:
        return domain, "must not contain wildcard characters."
    if domain == "localhost" or domain.endswith(".localhost"):
        return domain, "must not be localhost."

    try:
        ip = ipaddress.ip_address(domain)
    except ValueError:
        ip = None

    if ip is not None:
        return domain, "must not be an IP address."

    if not _DOMAIN_PATTERN.fullmatch(domain):
        return domain, "must be a simple domain name."

    labels = domain.split(".")
    for label in labels:
        if not _DOMAIN_LABEL_PATTERN.fullmatch(label):
            return domain, "must contain valid domain labels only."

    return domain, None


def _scan_forbidden_content(value: Any, errors: list[str], path: str = "manifest") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            key_lower = key_text.strip().lower()
            child_path = f"{path}.{key_text}" if path else key_text

            if key_lower in _FORBIDDEN_NESTED_KEYS:
                errors.append(f"Manifest contains forbidden field at {child_path}.")

            if key_lower in _FORBIDDEN_EXECUTION_TOKENS:
                errors.append(f"Manifest contains forbidden execution field at {child_path}.")

            _scan_forbidden_content(item, errors, child_path)
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            _scan_forbidden_content(item, errors, f"{path}[{index}]")
        return

    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _scan_forbidden_content(item, errors, f"{path}[{index}]")
        return

    if isinstance(value, str):
        text = value.strip().lower()
        if not text:
            return
        for pattern in _EXECUTION_WORD_PATTERNS:
            if pattern.search(text):
                errors.append(f"Manifest contains forbidden execution content at {path}.")
                return
        for token in ("npm install", "pip install", "docker run"):
            if token in text:
                errors.append(f"Manifest contains forbidden execution content at {path}.")
                return
