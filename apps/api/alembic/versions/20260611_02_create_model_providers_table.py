"""create model_providers table

Revision ID: 20260611_02
Revises: 20260611_01
Create Date: 2026-06-11 20:45:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260611_02"
down_revision = "20260611_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("provider_type", sa.String(length=40), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("auth_type", sa.String(length=40), nullable=False),
        sa.Column("secret_reference", sa.Text(), nullable=True),
        sa.Column("default_model", sa.String(length=120), nullable=True),
        sa.Column("fallback_provider_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="active", nullable=False),
        sa.Column("is_private", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
            ["fallback_provider_id"],
            ["model_providers.id"],
            name="fk_model_providers_fallback_provider_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_model_providers_provider_type",
        "model_providers",
        ["provider_type"],
        unique=False,
    )
    op.create_index(
        "ix_model_providers_status",
        "model_providers",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_model_providers_status", table_name="model_providers")
    op.drop_index("ix_model_providers_provider_type", table_name="model_providers")
    op.drop_table("model_providers")
