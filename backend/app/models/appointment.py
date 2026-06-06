"""Appointment SQLAlchemy model."""
import uuid
import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from backend.app.models.lead import Lead
from backend.app.models.agent import Agent
from backend.app.models.property import Property

class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class MeetingType(str, enum.Enum):
    ONSITE = "onsite"
    VIDEO_CALL = "video_call"
    PHONE_CALL = "phone_call"

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    property_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("properties.id", ondelete="SET NULL"), nullable=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    meeting_type: Mapped[MeetingType] = mapped_column(
        Enum(MeetingType),
        default=MeetingType.ONSITE,
        nullable=False,
        index=True,
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus),
        default=AppointmentStatus.PENDING,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    google_event_id: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    lead: Mapped["Lead"] = relationship(back_populates="appointments")
    agent: Mapped["Agent"] = relationship(back_populates="appointments")
    property: Mapped["Property"] = relationship(
        back_populates="appointments"
    )
