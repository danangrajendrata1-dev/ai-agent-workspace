"""create github_imports table

Revision ID: 20260611_05
Revises: 20260611_04
Create Date: 2026-06-11 22:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260611_05"
down_revision = "20260611_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_imports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repo_url", sa.Text(), nullable=False),
        sa.Column("branch", sa.String(length=120), nullable=True),
        sa.Column("commit_sha", sa.String(length=120), nullable=True),
        sa.Column("import_type", sa.String(length=30), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("content_preview", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="preview", nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_github_imports_repo_url", "github_imports", ["repo_url"], unique=False)
    op.create_index("ix_github_imports_status", "github_imports", ["status"], unique=False)
    op.create_index("ix_github_imports_commit_sha", "github_imports", ["commit_sha"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_github_imports_commit_sha", table_name="github_imports")
    op.drop_index("ix_github_imports_status", table_name="github_imports")
    op.drop_index("ix_github_imports_repo_url", table_name="github_imports")
    op.drop_table("github_imports")
