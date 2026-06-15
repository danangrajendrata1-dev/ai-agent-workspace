import uuid

from sqlalchemy import ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from app.models.base import Base


class HandoffDraft(Base):
    __tablename__ = "handoff_drafts"
    __table_args__ = (
        Index("ix_handoff_drafts_owner_id_created_at", "owner_id", "created_at"),
        Index("ix_handoff_drafts_selected_agent_id", "selected_agent_id"),
        Index("ix_handoff_drafts_recommended_agent_id", "recommended_agent_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    routing_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    routing_reasons: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    recommended_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    selected_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    active_skill_matches: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    draft_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
