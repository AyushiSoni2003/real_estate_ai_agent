from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from backend.app.models.property import Property
from datetime import datetime
import uuid
import enum

class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    FLOOR_PLAN = "floor_plan"
    VIRTUAL_TOUR = "virtual_tour"


class PropertyMedia(Base):
    __tablename__ = "property_media"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    media_type: Mapped[MediaType] = mapped_column(
        Enum(MediaType),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    property: Mapped["Property"] = relationship(
        back_populates="media_files"
    )