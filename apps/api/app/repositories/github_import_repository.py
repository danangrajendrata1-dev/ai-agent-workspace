import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.github_import import GitHubImport


def create_preview(db: Session, import_data: dict) -> GitHubImport:
    github_import = GitHubImport(**import_data)
    db.add(github_import)
    db.flush()
    return github_import


def get_by_id(db: Session, import_id: uuid.UUID) -> GitHubImport | None:
    statement = select(GitHubImport).where(GitHubImport.id == import_id)
    return db.execute(statement).scalar_one_or_none()


def get_by_id_for_owner(db: Session, import_id: uuid.UUID, owner_id: uuid.UUID) -> GitHubImport | None:
    statement = select(GitHubImport).where(
        GitHubImport.id == import_id,
        GitHubImport.owner_id == owner_id,
    )
    return db.execute(statement).scalar_one_or_none()


def list_imports(db: Session, owner_id: uuid.UUID | None = None) -> list[GitHubImport]:
    statement = select(GitHubImport)
    if owner_id is not None:
        statement = statement.where(GitHubImport.owner_id == owner_id)
    statement = statement.order_by(GitHubImport.created_at.desc())
    return list(db.execute(statement).scalars().all())


def update_status(db: Session, github_import: GitHubImport, status: str) -> GitHubImport:
    github_import.status = status
    db.add(github_import)
    db.flush()
    return github_import


def update_review_notes(
    db: Session,
    github_import: GitHubImport,
    review_notes: str | None,
) -> GitHubImport:
    github_import.review_notes = review_notes
    db.add(github_import)
    db.flush()
    return github_import
