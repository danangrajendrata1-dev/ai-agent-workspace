"""add subscription plan and default user role

Revision ID: 20260615_01
Revises: 20260612_04
Create Date: 2026-06-15 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260615_01"
down_revision = "20260612_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "subscription_plan",
            sa.String(length=30),
            server_default=sa.text("'free'"),
            nullable=False,
        ),
    )
    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=50),
        server_default=sa.text("'user'"),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=50),
        server_default=sa.text("'owner'"),
        existing_nullable=False,
    )
    op.drop_column("users", "subscription_plan")
