from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any


MAX_CONTENT_LENGTH = 200_000

_FORBIDDEN_EXECUTION_MARKERS = (
    "eval(",
    "exec(",
    "subprocess",
    "os.system",
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
)

_FORBIDDEN_SECRET_MARKERS = (
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "private_key",
    "client_secret",
    "password=",
    "token=",
    ".env",
)

_FENCED_BLOCK_PATTERN = re.compile(r"```([^\n`]*)\n(.*?)```", re.DOTALL)


@dataclass(slots=True)
class SkillManifestExtractionResult:
    is_extracted: bool
    manifest: dict[str, Any] | None
    errors: list[str]
    warnings: list[str]
    source_format: str | None


def extract_skill_manifest_from_text(content: str) -> SkillManifestExtractionResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(content, str):
        return SkillManifestExtractionResult(
            is_extracted=False,
            manifest=None,
            errors=["Content must be a string."],
            warnings=warnings,
            source_format=None,
        )

    if len(content) > MAX_CONTENT_LENGTH:
        return SkillManifestExtractionResult(
            is_extracted=False,
            manifest=None,
            errors=[f"Content exceeds maximum length of {MAX_CONTENT_LENGTH} characters."],
            warnings=warnings,
            source_format=None,
        )

    stripped_content = content.strip()
    if not stripped_content:
        return SkillManifestExtractionResult(
            is_extracted=False,
            manifest=None,
            errors=["Content is empty."],
            warnings=warnings,
            source_format=None,
        )

    fences = list(_FENCED_BLOCK_PATTERN.finditer(stripped_content))
    if fences:
        if len(fences) != 1:
            return SkillManifestExtractionResult(
                is_extracted=False,
                manifest=None,
                errors=["Exactly one JSON fenced block is required."],
                warnings=warnings,
                source_format=None,
            )

        fence = fences[0]
        fence_language = fence.group(1).strip().lower()
        if fence_language not in {"", "json"}:
            return SkillManifestExtractionResult(
                is_extracted=False,
                manifest=None,
                errors=[f"Unsupported fenced code block language: {fence_language or 'plain'}."],
                warnings=warnings,
                source_format=None,
            )

        forbidden_error = _find_forbidden_marker(stripped_content)
        if forbidden_error is not None:
            return SkillManifestExtractionResult(
                is_extracted=False,
                manifest=None,
                errors=[forbidden_error],
                warnings=warnings,
                source_format=None,
            )

        fence_content = fence.group(2).strip()
        if not fence_content:
            return SkillManifestExtractionResult(
                is_extracted=False,
                manifest=None,
                errors=["JSON fenced block is empty."],
                warnings=warnings,
                source_format=None,
            )

        fence_object = _parse_json_object(fence_content)
        if fence_object is None:
            return SkillManifestExtractionResult(
                is_extracted=False,
                manifest=None,
                errors=["JSON fenced block is invalid JSON."],
                warnings=warnings,
                source_format=None,
            )
        if not isinstance(fence_object, dict):
            return SkillManifestExtractionResult(
                is_extracted=False,
                manifest=None,
                errors=["JSON fenced block must contain a JSON object."],
                warnings=warnings,
                source_format=None,
            )

        heading_match = re.search(r"(?im)^\s*#{1,6}\s*.*skill manifest.*$", stripped_content)
        if heading_match is not None:
            warnings.append("Skill manifest heading found.")

        return SkillManifestExtractionResult(
            is_extracted=True,
            manifest=fence_object,
            errors=errors,
            warnings=warnings,
            source_format="markdown_json_fence",
        )

    forbidden_error = _find_forbidden_marker(stripped_content)
    if forbidden_error is not None:
        return SkillManifestExtractionResult(
            is_extracted=False,
            manifest=None,
            errors=[forbidden_error],
            warnings=warnings,
            source_format=None,
        )

    json_object = _parse_json_object(stripped_content)
    if isinstance(json_object, dict):
        return SkillManifestExtractionResult(
            is_extracted=True,
            manifest=json_object,
            errors=errors,
            warnings=warnings,
            source_format="json",
        )
    if json_object is not None:
        return SkillManifestExtractionResult(
            is_extracted=False,
            manifest=None,
            errors=["JSON content must be an object."],
            warnings=warnings,
            source_format=None,
        )

    if not fences:
        return SkillManifestExtractionResult(
            is_extracted=False,
            manifest=None,
            errors=["No JSON manifest found."],
            warnings=warnings,
            source_format=None,
        )


def _parse_json_object(text: str) -> dict[str, Any] | list[Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, list):
        return parsed
    return None


def _find_forbidden_marker(text: str) -> str | None:
    lowered = text.lower()
    for marker in _FORBIDDEN_EXECUTION_MARKERS:
        if marker in lowered:
            return f"Content contains forbidden execution marker: {marker}."
    for marker in _FORBIDDEN_SECRET_MARKERS:
        if marker in lowered:
            return f"Content contains forbidden secret marker: {marker}."
    return None
