"""create handoff drafts table

Revision ID: 20260616_01_create_handoff_drafts_table
Revises: 20260615_03_create_model_provider_api_keys_table
Create Date: 2026-06-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260616_01_create_handoff_drafts_table"
down_revision = "20260615_03_create_model_provider_api_keys_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "handoff_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("task_text", sa.Text(), nullable=False),
        sa.Column("routing_confidence", sa.String(length=20), nullable=True),
        sa.Column("routing_reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "recommended_agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "selected_agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("active_skill_matches", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "draft_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_handoff_drafts_owner_id_created_at",
        "handoff_drafts",
        ["owner_id", "created_at"],
    )
    op.create_index(
        "ix_handoff_drafts_selected_agent_id",
        "handoff_drafts",
        ["selected_agent_id"],
    )
    op.create_index(
        "ix_handoff_drafts_recommended_agent_id",
        "handoff_drafts",
        ["recommended_agent_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_handoff_drafts_recommended_agent_id", table_name="handoff_drafts")
    op.drop_index("ix_handoff_drafts_selected_agent_id", table_name="handoff_drafts")
    op.drop_index("ix_handoff_drafts_owner_id_created_at", table_name="handoff_drafts")
    op.drop_table("handoff_drafts")
