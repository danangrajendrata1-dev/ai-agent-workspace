"""add revoked_at to workflow consents

Revision ID: 20260617_03
Revises: 20260617_02
Create Date: 2026-06-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260617_03"
down_revision = "20260617_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflow_consents",
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workflow_consents", "revoked_at")
