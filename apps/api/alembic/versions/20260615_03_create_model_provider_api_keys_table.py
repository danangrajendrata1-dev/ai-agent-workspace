"""create model_provider_api_keys table

Revision ID: 20260615_03
Revises: 20260615_02
Create Date: 2026-06-15 11:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260615_03"
down_revision = "20260615_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_provider_api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("encrypted_api_key", sa.Text(), nullable=False),
        sa.Column("key_last4", sa.String(length=4), nullable=False),
        sa.Column(
            "key_prefix_masked",
            sa.String(length=16),
            server_default="********",
            nullable=False,
        ),
        sa.Column(
            "connection_status",
            sa.String(length=30),
            server_default="connected",
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name="fk_model_provider_api_keys_owner_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "provider", name="uq_model_provider_api_keys_owner_provider"),
    )


def downgrade() -> None:
    op.drop_table("model_provider_api_keys")
