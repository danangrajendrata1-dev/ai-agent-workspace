"""create chat sessions table

Revision ID: 20260617_01
Revises: 20260616_01
Create Date: 2026-06-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260617_01"
down_revision = "20260616_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("session_type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("messages_encrypted", sa.Text(), nullable=False),
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
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])
    op.create_index("ix_chat_sessions_user_id_updated_at", "chat_sessions", ["user_id", "updated_at"])
    op.create_index("ix_chat_sessions_agent_id", "chat_sessions", ["agent_id"])


def downgrade() -> None:
    op.drop_index("ix_chat_sessions_agent_id", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_user_id_updated_at", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_user_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")
