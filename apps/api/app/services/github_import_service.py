import re
import uuid

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.integrations.github_client import fetch_text_preview
from app.repositories import github_import_repository, skill_repository
from app.schemas.github_import import (
    GitHubImportRejectRequest,
    GitHubImportResponse,
    GitHubSkillImportApproveRequest,
    GitHubSkillPreviewRequest,
)
from app.services import log_service
from app.services.skill_manifest_pipeline_service import inspect_skill_manifest_content
from app.services.skill_manifest_risk_service import assess_skill_manifest_risk
from app.services.skill_markdown_instruction_service import (
    inspect_markdown_instruction_skill,
)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:150] or "skill"


def ensure_unique_skill_slug(
    db: Session,
    *,
    slug: str,
) -> str:
    existing = skill_repository.get_by_slug(db, slug)
    if existing is None:
        return slug
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Skill slug is already in use.",
    )


def serialize_github_import(github_import) -> GitHubImportResponse:
    response_data = GitHubImportResponse.model_validate(github_import).model_dump()
    response_data.update(_build_import_inspection_metadata(github_import.content_preview))
    return GitHubImportResponse.model_validate(response_data)


def _build_import_inspection_metadata(content_preview: str | None) -> dict:
    if not isinstance(content_preview, str) or not content_preview.strip():
        return {
            "skill_import_type": None,
            "inspection_warnings": [],
            "inspection_errors": [],
            "resource_paths": [],
            "safe_resource_paths": [],
            "risky_resource_paths": [],
            "blocked_resource_paths": [],
            "has_executable_resources": False,
            "requires_review": False,
        }

    manifest_inspection = inspect_skill_manifest_content(content_preview)
    if manifest_inspection.is_extracted:
        return {
            "skill_import_type": "manifest_skill",
            "inspection_warnings": manifest_inspection.warnings,
            "inspection_errors": manifest_inspection.errors,
            "resource_paths": [],
            "safe_resource_paths": [],
            "risky_resource_paths": [],
            "blocked_resource_paths": [],
            "has_executable_resources": False,
            "requires_review": bool(manifest_inspection.warnings or manifest_inspection.errors),
        }

    markdown_inspection = inspect_markdown_instruction_skill(content_preview)
    return {
        "skill_import_type": markdown_inspection.skill_import_type,
        "inspection_warnings": markdown_inspection.warnings,
        "inspection_errors": markdown_inspection.errors,
        "resource_paths": markdown_inspection.resource_paths,
        "safe_resource_paths": markdown_inspection.safe_resource_paths,
        "risky_resource_paths": markdown_inspection.risky_resource_paths,
        "blocked_resource_paths": markdown_inspection.blocked_resource_paths,
        "has_executable_resources": markdown_inspection.has_executable_resources,
        "requires_review": markdown_inspection.requires_review,
    }


def _safe_record_import_log(record_fn, db: Session, **kwargs) -> None:
    try:
        record_fn(db, **kwargs)
    except Exception:
        db.rollback()


def _normalize_fetch_preview_result(fetch_result):
    if hasattr(fetch_result, "raw_url") and hasattr(fetch_result, "content"):
        return fetch_result

    if isinstance(fetch_result, tuple):
        if len(fetch_result) == 2:
            raw_url, content = fetch_result
            return type(
                "LegacyGitHubPreviewFetchResult",
                (),
                {
                    "raw_url": raw_url,
                    "content": content,
                    "commit_sha": None,
                    "source_identity": None,
                    "source_identity_type": None,
                },
            )()

        if len(fetch_result) == 3:
            raw_url, content, commit_sha = fetch_result
            return type(
                "LegacyGitHubPreviewFetchResult",
                (),
                {
                    "raw_url": raw_url,
                    "content": content,
                    "commit_sha": commit_sha,
                    "source_identity": commit_sha,
                    "source_identity_type": "commit_sha" if commit_sha else None,
                },
            )()

    raise ValueError("Unsupported GitHub preview fetch result.")


def _is_dangerous_manifest_failure(errors: list[str]) -> bool:
    danger_markers = (
        "forbidden execution marker",
        "forbidden secret marker",
        "forbidden execution content",
        "Manifest contains forbidden field",
        "Manifest contains forbidden execution field",
        "Manifest contains forbidden execution content",
    )
    for error in errors:
        lowered = error.lower()
        if any(marker.lower() in lowered for marker in danger_markers):
            return True
    return False


def preview_github_skill(db: Session, payload: GitHubSkillPreviewRequest) -> GitHubImportResponse:
    try:
        fetch_result = _normalize_fetch_preview_result(
            fetch_text_preview(
            payload.repo_url,
            payload.branch,
            payload.file_path,
        )
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not fetch the requested GitHub file.",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    github_import = github_import_repository.create_preview(
        db,
        {
            "repo_url": payload.repo_url,
            "branch": payload.branch,
            "commit_sha": fetch_result.commit_sha,
            "import_type": "skill",
            "file_path": payload.file_path,
            "content_preview": fetch_result.content,
            "status": "preview",
            "review_notes": None,
        },
    )
    db.commit()
    db.refresh(github_import)
    _safe_record_import_log(
        log_service.record_activity,
        db,
        request_id=None,
        actor_type="system",
        actor_id=None,
        event_type="github_import_preview_created",
        message="GitHub skill import preview created.",
        metadata_json={
            "import_id": str(github_import.id),
            "repo_url": github_import.repo_url,
            "branch": github_import.branch,
            "file_path": github_import.file_path,
            "import_type": github_import.import_type,
            "status": github_import.status,
            "commit_sha": github_import.commit_sha,
            "source_identity": fetch_result.source_identity,
            "source_identity_type": fetch_result.source_identity_type,
        },
    )
    db.commit()
    return serialize_github_import(github_import)


def list_github_imports(db: Session) -> list[GitHubImportResponse]:
    github_imports = github_import_repository.list_imports(db)
    return [serialize_github_import(item) for item in github_imports]


def get_github_import(db: Session, import_id: uuid.UUID) -> GitHubImportResponse:
    github_import = github_import_repository.get_by_id(db, import_id)
    if github_import is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub import not found.",
        )
    return serialize_github_import(github_import)


def approve_github_skill_import(
    db: Session,
    import_id: uuid.UUID,
    payload: GitHubSkillImportApproveRequest,
) -> GitHubImportResponse:
    github_import = github_import_repository.get_by_id(db, import_id)
    if github_import is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub import not found.",
        )
    if github_import.import_type != "skill":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only skill imports can be approved in this step.",
        )
    if github_import.status != "preview":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only preview imports can be approved.",
        )
    if not github_import.content_preview:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Import preview content is missing.",
        )

    skill_import_type = None
    risk_level = None
    inspection = inspect_skill_manifest_content(github_import.content_preview)
    if inspection.is_safe:
        skill_import_type = "manifest_skill"
        risk_result = assess_skill_manifest_risk(inspection.normalized_manifest or {})
        if risk_result.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skill manifest risk assessment blocked: " + "; ".join(risk_result.reasons),
            )
        risk_level = risk_result.risk_level
    elif inspection.is_extracted:
        _safe_record_import_log(
            log_service.record_activity,
            db,
            request_id=None,
            actor_type="system",
            actor_id=None,
            event_type="github_import_safety_check_failed",
            message="GitHub skill import blocked by manifest safety check.",
            metadata_json={
                "import_id": str(github_import.id),
                "repo_url": github_import.repo_url,
                "branch": github_import.branch,
                "file_path": github_import.file_path,
                "import_type": github_import.import_type,
                "skill_import_type": "manifest_skill",
                "status": github_import.status,
                "commit_sha": github_import.commit_sha,
                "error_count": len(inspection.errors),
                "error_summary": inspection.errors[:5],
            },
        )
        _safe_record_import_log(
            log_service.record_audit,
            db,
            user_id=None,
            action="github_import_safety_check_failed",
            entity_type="github_import",
            entity_id=github_import.id,
            before_data={
                "status": github_import.status,
                "review_notes": github_import.review_notes,
            },
            after_data={
                "status": github_import.status,
                "review_notes": github_import.review_notes,
                "error_count": len(inspection.errors),
                "commit_sha": github_import.commit_sha,
            },
            ip_address=None,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill manifest safety check failed: " + "; ".join(inspection.errors),
        )
    elif _is_dangerous_manifest_failure(inspection.errors):
        _safe_record_import_log(
            log_service.record_activity,
            db,
            request_id=None,
            actor_type="system",
            actor_id=None,
            event_type="github_import_safety_check_failed",
            message="GitHub skill import blocked by manifest safety check.",
            metadata_json={
                "import_id": str(github_import.id),
                "repo_url": github_import.repo_url,
                "branch": github_import.branch,
                "file_path": github_import.file_path,
                "import_type": github_import.import_type,
                "skill_import_type": "manifest_skill",
                "status": github_import.status,
                "commit_sha": github_import.commit_sha,
                "error_count": len(inspection.errors),
                "error_summary": inspection.errors[:5],
            },
        )
        _safe_record_import_log(
            log_service.record_audit,
            db,
            user_id=None,
            action="github_import_safety_check_failed",
            entity_type="github_import",
            entity_id=github_import.id,
            before_data={
                "status": github_import.status,
                "review_notes": github_import.review_notes,
            },
            after_data={
                "status": github_import.status,
                "review_notes": github_import.review_notes,
                "error_count": len(inspection.errors),
                "commit_sha": github_import.commit_sha,
            },
            ip_address=None,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill manifest safety check failed: " + "; ".join(inspection.errors),
        )

    else:
        markdown_inspection = inspect_markdown_instruction_skill(github_import.content_preview)
        if not markdown_inspection.is_safe:
            _safe_record_import_log(
                log_service.record_activity,
                db,
                request_id=None,
                actor_type="system",
                actor_id=None,
                event_type="github_import_safety_check_failed",
                message="GitHub skill import blocked by markdown instruction safety check.",
                metadata_json={
                    "import_id": str(github_import.id),
                    "repo_url": github_import.repo_url,
                    "branch": github_import.branch,
                    "file_path": github_import.file_path,
                    "import_type": github_import.import_type,
                    "skill_import_type": markdown_inspection.skill_import_type,
                    "status": github_import.status,
                    "commit_sha": github_import.commit_sha,
                    "risk_level": markdown_inspection.risk_level,
                    "error_count": len(markdown_inspection.errors),
                    "error_summary": markdown_inspection.errors[:5],
                },
            )
            _safe_record_import_log(
                log_service.record_audit,
                db,
                user_id=None,
                action="github_import_safety_check_failed",
                entity_type="github_import",
                entity_id=github_import.id,
                before_data={
                    "status": github_import.status,
                    "review_notes": github_import.review_notes,
                },
                after_data={
                    "status": github_import.status,
                    "review_notes": github_import.review_notes,
                    "error_count": len(markdown_inspection.errors),
                    "risk_level": markdown_inspection.risk_level,
                    "commit_sha": github_import.commit_sha,
                },
                ip_address=None,
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skill markdown instruction safety check failed: "
                + "; ".join(markdown_inspection.errors),
            )
        skill_import_type = markdown_inspection.skill_import_type
        risk_level = markdown_inspection.risk_level

    if risk_level is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill import risk level could not be determined.",
        )

    slug = ensure_unique_skill_slug(db, slug=slugify(payload.slug or payload.name))
    skill_status = payload.status if payload.status in {"inactive", "disabled"} else "inactive"

    skill = skill_repository.create(
        db,
        {
            "name": payload.name,
            "slug": slug,
            "description": payload.description,
            "content": github_import.content_preview,
            "source_type": "github",
            "source_id": github_import.id,
            "version_label": payload.version_label,
            "risk_level": risk_level,
            "status": skill_status,
        },
    )
    github_import_repository.update_status(db, github_import, "imported")
    github_import_repository.update_review_notes(db, github_import, payload.review_notes)
    db.commit()
    db.refresh(github_import)
    _safe_record_import_log(
        log_service.record_activity,
        db,
        request_id=None,
        actor_type="system",
        actor_id=None,
        event_type="github_import_skill_imported",
        message="GitHub skill import approved and saved.",
        metadata_json={
            "import_id": str(github_import.id),
            "skill_id": str(skill.id),
            "repo_url": github_import.repo_url,
            "branch": github_import.branch,
            "file_path": github_import.file_path,
            "import_type": github_import.import_type,
            "skill_import_type": skill_import_type,
            "status": github_import.status,
            "commit_sha": github_import.commit_sha,
            "risk_level": risk_level,
            "skill_status": skill.status,
        },
    )
    _safe_record_import_log(
        log_service.record_audit,
        db,
        user_id=None,
        action="github_import_skill_imported",
        entity_type="github_import",
        entity_id=github_import.id,
        before_data={
            "status": "preview",
            "review_notes": None,
        },
        after_data={
            "status": github_import.status,
            "review_notes": github_import.review_notes,
            "skill_id": str(skill.id),
            "skill_import_type": skill_import_type,
            "risk_level": risk_level,
            "skill_status": skill.status,
            "commit_sha": github_import.commit_sha,
        },
        ip_address=None,
    )
    db.commit()
    return serialize_github_import(github_import)


def reject_github_import(
    db: Session,
    import_id: uuid.UUID,
    payload: GitHubImportRejectRequest,
) -> GitHubImportResponse:
    github_import = github_import_repository.get_by_id(db, import_id)
    if github_import is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub import not found.",
        )
    github_import_repository.update_status(db, github_import, "rejected")
    github_import_repository.update_review_notes(db, github_import, payload.review_notes)
    db.commit()
    db.refresh(github_import)
    _safe_record_import_log(
        log_service.record_activity,
        db,
        request_id=None,
        actor_type="system",
        actor_id=None,
        event_type="github_import_rejected",
        message="GitHub import rejected.",
        metadata_json={
            "import_id": str(github_import.id),
            "repo_url": github_import.repo_url,
            "branch": github_import.branch,
            "file_path": github_import.file_path,
            "import_type": github_import.import_type,
            "status": github_import.status,
            "commit_sha": github_import.commit_sha,
        },
    )
    _safe_record_import_log(
        log_service.record_audit,
        db,
        user_id=None,
        action="github_import_rejected",
        entity_type="github_import",
        entity_id=github_import.id,
        before_data={
            "status": "preview",
            "review_notes": None,
        },
        after_data={
            "status": github_import.status,
            "review_notes": github_import.review_notes,
            "commit_sha": github_import.commit_sha,
        },
        ip_address=None,
    )
    db.commit()
    return serialize_github_import(github_import)


def disable_github_import(db: Session, import_id: uuid.UUID) -> GitHubImportResponse:
    github_import = github_import_repository.get_by_id(db, import_id)
    if github_import is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub import not found.",
        )
    github_import_repository.update_status(db, github_import, "disabled")
    db.commit()
    db.refresh(github_import)
    _safe_record_import_log(
        log_service.record_activity,
        db,
        request_id=None,
        actor_type="system",
        actor_id=None,
        event_type="github_import_disabled",
        message="GitHub import disabled.",
        metadata_json={
            "import_id": str(github_import.id),
            "repo_url": github_import.repo_url,
            "branch": github_import.branch,
            "file_path": github_import.file_path,
            "import_type": github_import.import_type,
            "status": github_import.status,
            "commit_sha": github_import.commit_sha,
        },
    )
    _safe_record_import_log(
        log_service.record_audit,
        db,
        user_id=None,
        action="github_import_disabled",
        entity_type="github_import",
        entity_id=github_import.id,
        before_data={
            "status": "preview",
        },
        after_data={
            "status": github_import.status,
            "commit_sha": github_import.commit_sha,
        },
        ip_address=None,
    )
    db.commit()
    return serialize_github_import(github_import)
