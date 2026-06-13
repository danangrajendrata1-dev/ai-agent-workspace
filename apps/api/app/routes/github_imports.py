import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_owner
from app.schemas.github_import import (
    GitHubImportListResponse,
    GitHubImportRejectRequest,
    GitHubImportResponse,
    GitHubSkillImportApproveRequest,
    GitHubSkillPreviewRequest,
)
from app.services import github_import_service


router = APIRouter(prefix="/github-imports", tags=["github-imports"])


@router.post("/skills/preview", response_model=GitHubImportResponse, status_code=status.HTTP_201_CREATED)
def preview_github_skill(
    payload: GitHubSkillPreviewRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return github_import_service.preview_github_skill(db, payload)


@router.get("", response_model=GitHubImportListResponse)
def list_github_imports(
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return GitHubImportListResponse(items=github_import_service.list_github_imports(db))


@router.get("/{import_id}", response_model=GitHubImportResponse)
def get_github_import(
    import_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return github_import_service.get_github_import(db, import_id)


@router.post("/{import_id}/approve-skill", response_model=GitHubImportResponse)
def approve_github_skill_import(
    import_id: uuid.UUID,
    payload: GitHubSkillImportApproveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return github_import_service.approve_github_skill_import(db, import_id, payload)


@router.post("/{import_id}/reject", response_model=GitHubImportResponse)
def reject_github_import(
    import_id: uuid.UUID,
    payload: GitHubImportRejectRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return github_import_service.reject_github_import(db, import_id, payload)


@router.post("/{import_id}/disable", response_model=GitHubImportResponse)
def disable_github_import(
    import_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    return github_import_service.disable_github_import(db, import_id)
