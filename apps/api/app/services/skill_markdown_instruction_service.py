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
_SECRET_LEAK_PATTERNS = (
    re.compile(r"\bapi[_-]?key\b\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\baccess[_-]?token\b\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\brefresh[_-]?token\b\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\bclient[_-]?secret\b\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\bpassword\b\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\bcredential(?:s)?\b\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\bprivate[_-]?key\b\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\boauth[_-]?token\b\s*[:=]\s*\S+", re.IGNORECASE),
)


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

    secret_error = _find_secret_leak(content)
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

    if resource_result.risky_resource_paths or resource_result.has_executable_resources:
        risk_level = "high"
    elif resource_result.safe_resource_paths:
        risk_level = "medium"
    else:
        risk_level = "low"

    requires_review = bool(
        resource_result.safe_resource_paths
        or resource_result.risky_resource_paths
        or resource_result.blocked_resource_paths
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


def _find_secret_leak(content: str) -> str | None:
    if _PRIVATE_KEY_BLOCK_PATTERN.search(content):
        return "Content contains a private key block."

    for pattern in _SECRET_LEAK_PATTERNS:
        if pattern.search(content):
            return "Content contains secret, token, or credential leakage."

    return None
