"""create model_provider_settings table

Revision ID: 20260615_02
Revises: 20260615_01
Create Date: 2026-06-15 10:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260615_02"
down_revision = "20260615_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_provider_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("preferred_provider", sa.String(length=40), nullable=True),
        sa.Column("preferred_model", sa.String(length=120), nullable=True),
        sa.Column("connection_status", sa.String(length=30), server_default="not_connected", nullable=False),
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
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_model_provider_settings_owner_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", name="uq_model_provider_settings_owner_id"),
    )


def downgrade() -> None:
    op.drop_table("model_provider_settings")
