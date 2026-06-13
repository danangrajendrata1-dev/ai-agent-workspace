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
    return GitHubImportResponse.model_validate(github_import)


def preview_github_skill(db: Session, payload: GitHubSkillPreviewRequest) -> GitHubImportResponse:
    try:
        _, content_preview = fetch_text_preview(
            payload.repo_url,
            payload.branch,
            payload.file_path,
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
            "commit_sha": None,
            "import_type": "skill",
            "file_path": payload.file_path,
            "content_preview": content_preview,
            "status": "preview",
            "review_notes": None,
        },
    )
    db.commit()
    db.refresh(github_import)
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

    slug = ensure_unique_skill_slug(db, slug=slugify(payload.slug or payload.name))

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
            "risk_level": payload.risk_level,
            "status": payload.status,
        },
    )
    github_import_repository.update_status(db, github_import, "imported")
    github_import_repository.update_review_notes(db, github_import, payload.review_notes)
    db.commit()
    db.refresh(github_import)
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
    return serialize_github_import(github_import)
