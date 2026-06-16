import uuid

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from app.models.base import Base


class WorkflowSkillTemplateBinding(Base):
    __tablename__ = "workflow_skill_template_bindings"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "skill_id",
            "template_id",
            "template_version",
            name="uq_workflow_skill_template_bindings_user_skill_template_version",
        ),
        Index("ix_workflow_skill_template_bindings_user_id", "user_id"),
        Index("ix_workflow_skill_template_bindings_skill_id", "skill_id"),
        Index("ix_workflow_skill_template_bindings_user_id_template_id", "user_id", "template_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_id: Mapped[str] = mapped_column(String(100), nullable=False)
    template_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
