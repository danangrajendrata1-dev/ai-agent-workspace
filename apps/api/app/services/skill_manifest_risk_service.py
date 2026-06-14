from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SkillManifestRiskResult:
    risk_level: str
    reasons: list[str]
    requires_review: bool
    is_blocked: bool


def assess_skill_manifest_risk(normalized_manifest: dict) -> SkillManifestRiskResult:
    if not isinstance(normalized_manifest, dict):
        return SkillManifestRiskResult(
            risk_level="blocked",
            reasons=["Normalized manifest must be a dictionary."],
            requires_review=True,
            is_blocked=True,
        )

    required_credentials = _as_list(normalized_manifest.get("required_credentials"))
    required_domains = _as_list(normalized_manifest.get("required_domains"))
    required_tools = _as_list(normalized_manifest.get("required_tools"))
    permissions_requested = _as_list(normalized_manifest.get("permissions_requested"))
    required_capabilities = _as_list(normalized_manifest.get("required_capabilities"))
    n8n_workflow = normalized_manifest.get("n8n_workflow")

    if _has_invalid_collection(
        normalized_manifest,
        [
            "required_credentials",
            "required_domains",
            "required_tools",
            "permissions_requested",
            "required_capabilities",
        ],
    ):
        return SkillManifestRiskResult(
            risk_level="blocked",
            reasons=["Normalized manifest contains invalid collection field type."],
            requires_review=True,
            is_blocked=True,
        )

    if n8n_workflow is not None and not isinstance(n8n_workflow, dict):
        return SkillManifestRiskResult(
            risk_level="blocked",
            reasons=["Normalized manifest contains invalid n8n workflow metadata."],
            requires_review=True,
            is_blocked=True,
        )

    reasons: list[str] = []

    if required_credentials or required_tools or n8n_workflow is not None:
        if required_credentials:
            reasons.append("Credentials requested.")
        if required_tools:
            reasons.append("External tools requested.")
        if n8n_workflow is not None:
            reasons.append("n8n workflow metadata requested.")
        return SkillManifestRiskResult(
            risk_level="high",
            reasons=reasons,
            requires_review=True,
            is_blocked=False,
        )

    if required_domains or len(required_capabilities) > 1 or permissions_requested:
        if required_domains:
            reasons.append("Domain allowlist requested.")
        if len(required_capabilities) > 1:
            reasons.append("Multiple capabilities requested.")
        if permissions_requested:
            reasons.append("Permissions requested.")
        return SkillManifestRiskResult(
            risk_level="medium",
            reasons=reasons,
            requires_review=True,
            is_blocked=False,
        )

    reasons.append("Metadata-only manifest.")
    return SkillManifestRiskResult(
        risk_level="low",
        reasons=reasons,
        requires_review=False,
        is_blocked=False,
    )


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return []


def _has_invalid_collection(normalized_manifest: dict, field_names: list[str]) -> bool:
    for field_name in field_names:
        value = normalized_manifest.get(field_name)
        if value is None:
            continue
        if not isinstance(value, list):
            return True
    return False
