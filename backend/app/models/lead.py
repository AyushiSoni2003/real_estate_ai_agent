"""Lead SQLAlchemy model."""
import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from backend.app.models.appointment import Appointment
from backend.app.models.follow_up_log import FollowUpLog
from backend.app.models.message import Message
from backend.app.models.agent import Agent

class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    APPOINTMENT_SET = "appointment_set"
    CONVERTED = "converted"
    LOST = "lost"

class LeadSource(str, enum.Enum):
    WEBSITE = "website"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    WHATSAPP = "whatsapp"
    REFERRAL = "referral"

class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    source: Mapped[LeadSource | None] = mapped_column(
        Enum(LeadSource),
        nullable=True,
    )
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), default=LeadStatus.NEW, index=True
    )
    budget_min: Mapped[int | None] = mapped_column()
    budget_max: Mapped[int | None] = mapped_column()
    preferred_location: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    agent: Mapped["Agent"] = relationship(back_populates="leads")
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )
    follow_up_logs: Mapped[list["FollowUpLog"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )
