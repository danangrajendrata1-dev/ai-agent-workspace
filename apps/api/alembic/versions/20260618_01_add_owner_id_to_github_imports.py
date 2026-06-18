"""add owner_id to github imports

Revision ID: 20260618_01
Revises: 20260617_03
Create Date: 2026-06-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260618_01"
down_revision = "20260617_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "github_imports",
        sa.Column("owner_id", sa.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_github_imports_owner_id", "github_imports", ["owner_id"])
    op.create_foreign_key(
        "fk_github_imports_owner_id_users",
        "github_imports",
        "users",
        ["owner_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_github_imports_owner_id_users", "github_imports", type_="foreignkey")
    op.drop_index("ix_github_imports_owner_id", table_name="github_imports")
    op.drop_column("github_imports", "owner_id")
