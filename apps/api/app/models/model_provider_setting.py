import uuid

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from app.models.base import Base


class ModelProviderSetting(Base):
    __tablename__ = "model_provider_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    preferred_provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    preferred_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    connection_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="not_connected",
        server_default="not_connected",
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
