import uuid
import enum
from datetime import datetime
from sqlalchemy import DateTime,Enum,ForeignKey,JSON, func
from sqlalchemy.orm import Mapped,mapped_column, relationship
from typing import TYPE_CHECKING
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lead import Lead

class LeadActivityType(str, enum.Enum):
    LEAD_CREATED = "lead_created"
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_READ = "message_read"
    MESSAGE_REPLIED = "message_replied"
    PROPERTY_VIEWED = "property_viewed"
    APPOINTMENT_BOOKED = "appointment_booked"
    APPOINTMENT_COMPLETED = "appointment_completed"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    AI_RECOMMENDATION_GENERATED = "ai_recommendation_generated"

class LeadActivity(Base):
    __tablename__ = "lead_activities"
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_type: Mapped[LeadActivityType] = mapped_column(
        Enum(LeadActivityType),
        nullable=False,
        index=True,
    )
    event_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    lead: Mapped["Lead"] = relationship(
        back_populates="activities"
    )