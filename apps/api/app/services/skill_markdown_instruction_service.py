from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from app.services.skill_resource_detection_service import (
    detect_skill_resource_references,
)


_PRIVATE_KEY_BLOCK_PATTERN = re.compile(
    r"-----BEGIN [A-Z0-9 -]*PRIVATE KEY-----",
    re.IGNORECASE,
)
_GENERIC_SECRET_TERMS = (
    "password",
    "credential",
    "credentials",
    "token",
    "api key",
    "api_key",
    "api-key",
    "encrypt",
    "decrypt",
)
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(?P<name>[A-Z0-9_]*?(?:api[_-]?key|secret[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|private[_-]?key|oauth[_-]?token|password|token|credential(?:s)?))\b\s*[:=]\s*(?P<value>[^\n\r`]+)"
)
_KNOWN_SECRET_PREFIX_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{8,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\bye29\.[0-9A-Za-z._-]{20,}\b", re.IGNORECASE),
)
_CODE_BLOCK_PATTERN = re.compile(r"```")
_INDENTED_CODE_PATTERN = re.compile(r"(?m)^(?:\t| {4,})\S")
_COMMAND_EXAMPLE_PATTERN = re.compile(r"(?m)^\s*(?:\$\s*)?[\w./-]+\b.*--[\w-]+(?:=|\s|$)")
_FUNCTION_CALL_PATTERN = re.compile(r"\b[A-Za-z_][\w.]{0,80}\([^()\n]{0,160}\)")


@dataclass(slots=True)
class SkillMarkdownInstructionResult:
    skill_import_type: str
    is_safe: bool
    risk_level: str
    errors: list[str]
    warnings: list[str]
    resource_paths: list[str]
    safe_resource_paths: list[str]
    risky_resource_paths: list[str]
    blocked_resource_paths: list[str]
    has_executable_resources: bool
    requires_review: bool


def inspect_markdown_instruction_skill(content: str) -> SkillMarkdownInstructionResult:
    resource_result = detect_skill_resource_references(content)
    warnings = list(resource_result.warnings)
    errors: list[str] = []

    if not isinstance(content, str) or not content.strip():
        errors.append("Content must be a non-empty string.")
        return _build_result(
            risk_level="blocked",
            is_safe=False,
            errors=errors,
            warnings=warnings,
            resource_result=resource_result,
        )

    secret_warning = _find_generic_secret_warning(content)
    if secret_warning is not None:
        warnings.append(secret_warning)

    code_example_warning = _find_code_example_warning(content)
    if code_example_warning is not None:
        warnings.append(code_example_warning)

    secret_error = _find_real_secret_leak(content)
    if secret_error is not None:
        errors.append(secret_error)
        return _build_result(
            risk_level="blocked",
            is_safe=False,
            errors=errors,
            warnings=warnings,
            resource_result=resource_result,
        )

    if resource_result.blocked_resource_paths:
        errors.append(
            "Blocked resource reference(s) found: "
            + ", ".join(resource_result.blocked_resource_paths)
        )
        return _build_result(
            risk_level="blocked",
            is_safe=False,
            errors=errors,
            warnings=warnings,
            resource_result=resource_result,
        )

    has_code_examples = code_example_warning is not None

    if resource_result.risky_resource_paths or resource_result.has_executable_resources:
        risk_level = "high"
    elif has_code_examples and _has_command_example(content):
        risk_level = "high"
    elif has_code_examples or resource_result.safe_resource_paths:
        risk_level = "medium"
    elif secret_warning is not None:
        risk_level = "low"
    else:
        risk_level = "low"

    requires_review = bool(
        resource_result.safe_resource_paths
        or resource_result.risky_resource_paths
        or resource_result.blocked_resource_paths
        or has_code_examples
    )

    return SkillMarkdownInstructionResult(
        skill_import_type="markdown_instruction",
        is_safe=True,
        risk_level=risk_level,
        errors=[],
        warnings=warnings,
        resource_paths=resource_result.resource_paths,
        safe_resource_paths=resource_result.safe_resource_paths,
        risky_resource_paths=resource_result.risky_resource_paths,
        blocked_resource_paths=resource_result.blocked_resource_paths,
        has_executable_resources=resource_result.has_executable_resources,
        requires_review=requires_review,
    )


def _build_result(
    *,
    risk_level: str,
    is_safe: bool,
    errors: list[str],
    warnings: list[str],
    resource_result: Any,
) -> SkillMarkdownInstructionResult:
    requires_review = bool(
        getattr(resource_result, "safe_resource_paths", [])
        or getattr(resource_result, "risky_resource_paths", [])
        or getattr(resource_result, "blocked_resource_paths", [])
    )
    return SkillMarkdownInstructionResult(
        skill_import_type="markdown_instruction",
        is_safe=is_safe,
        risk_level=risk_level,
        errors=errors,
        warnings=warnings,
        resource_paths=list(getattr(resource_result, "resource_paths", [])),
        safe_resource_paths=list(getattr(resource_result, "safe_resource_paths", [])),
        risky_resource_paths=list(getattr(resource_result, "risky_resource_paths", [])),
        blocked_resource_paths=list(getattr(resource_result, "blocked_resource_paths", [])),
        has_executable_resources=bool(getattr(resource_result, "has_executable_resources", False)),
        requires_review=requires_review,
    )


def _find_real_secret_leak(content: str) -> str | None:
    if _PRIVATE_KEY_BLOCK_PATTERN.search(content):
        return "Content contains a private key block."

    for pattern in _KNOWN_SECRET_PREFIX_PATTERNS:
        if pattern.search(content):
            return "Content contains secret, token, or credential leakage."

    for match in _SECRET_ASSIGNMENT_PATTERN.finditer(content):
        value = _normalize_secret_candidate_value(match.group("value"))
        if _is_secret_like_value(value):
            return "Content contains secret, token, or credential leakage."

    return None


def _find_generic_secret_warning(content: str) -> str | None:
    lowered = content.lower()
    if any(term in lowered for term in _GENERIC_SECRET_TERMS):
        return "Instructional secret-related terms detected; review recommended."
    return None


def _find_code_example_warning(content: str) -> str | None:
    if _CODE_BLOCK_PATTERN.search(content):
        return "Code block detected; review recommended."
    if _INDENTED_CODE_PATTERN.search(content):
        return "Indented code example detected; review recommended."
    if _COMMAND_EXAMPLE_PATTERN.search(content):
        return "Command example detected; review recommended."
    if _FUNCTION_CALL_PATTERN.search(content):
        return "Code example detected; review recommended."
    return None


def _has_command_example(content: str) -> bool:
    return _COMMAND_EXAMPLE_PATTERN.search(content) is not None


def _normalize_secret_candidate_value(value: str) -> str:
    cleaned = value.strip().strip("\"'`")
    cleaned = cleaned.rstrip(".,;:)")
    return cleaned


def _is_secret_like_value(value: str) -> bool:
    if not value:
        return False

    lowered = value.lower()
    if lowered.startswith("-----begin "):
        return True
    if any(pattern.search(value) for pattern in _KNOWN_SECRET_PREFIX_PATTERNS):
        return True

    if len(value) < 16:
        return False

    if any(char.isdigit() for char in value) and any(not char.isalnum() for char in value):
        return True

    if re.fullmatch(r"[A-Za-z0-9._-]{16,}", value) and ("-" in value or "_" in value or "." in value):
        return True

    if re.fullmatch(r"[A-Za-z0-9+/]{20,}={0,2}", value):
        return True

    if re.fullmatch(r"[A-Fa-f0-9]{24,}", value):
        return True

    return False
