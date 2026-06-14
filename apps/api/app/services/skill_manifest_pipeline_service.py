from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.skill_manifest_extraction_service import (
    extract_skill_manifest_from_text,
)
from app.services.skill_manifest_validation_service import (
    SkillManifestValidationResult,
    validate_skill_manifest,
)


@dataclass(slots=True)
class SkillManifestInspectionResult:
    is_safe: bool
    is_extracted: bool
    is_valid: bool
    manifest: dict[str, Any] | None
    normalized_manifest: dict[str, Any] | None
    errors: list[str]
    warnings: list[str]
    source_format: str | None


def inspect_skill_manifest_content(content: str) -> SkillManifestInspectionResult:
    extraction_result = extract_skill_manifest_from_text(content)
    warnings = list(extraction_result.warnings)

    if not extraction_result.is_extracted or extraction_result.manifest is None:
        return SkillManifestInspectionResult(
            is_safe=False,
            is_extracted=False,
            is_valid=False,
            manifest=None,
            normalized_manifest=None,
            errors=_prefix_messages("extraction", extraction_result.errors),
            warnings=warnings,
            source_format=extraction_result.source_format,
        )

    validation_result = validate_skill_manifest(extraction_result.manifest)
    warnings.extend(validation_result.warnings)

    if not validation_result.is_valid or validation_result.normalized_manifest is None:
        return SkillManifestInspectionResult(
            is_safe=False,
            is_extracted=True,
            is_valid=False,
            manifest=extraction_result.manifest,
            normalized_manifest=None,
            errors=_prefix_messages("validation", validation_result.errors),
            warnings=warnings,
            source_format=extraction_result.source_format,
        )

    return SkillManifestInspectionResult(
        is_safe=True,
        is_extracted=True,
        is_valid=True,
        manifest=extraction_result.manifest,
        normalized_manifest=validation_result.normalized_manifest,
        errors=[],
        warnings=warnings,
        source_format=extraction_result.source_format,
    )


def _prefix_messages(prefix: str, messages: list[str]) -> list[str]:
    return [f"{prefix}: {message}" for message in messages]
