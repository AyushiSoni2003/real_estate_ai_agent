import uuid
import enum
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String,Text,Integer,DateTime,Enum,ForeignKey,func
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lead import Lead

class AIInteractionType(str, enum.Enum):
    FOLLOW_UP_MESSAGE = "follow_up_message"
    PROPERTY_RECOMMENDATION = "property_recommendation"
    LEAD_SUMMARY = "lead_summary"
    APPOINTMENT_ASSISTANT = "appointment_assistant"

class AIInteraction(Base):
    __tablename__ = "ai_interactions"
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    interaction_type: Mapped[AIInteractionType] = mapped_column(
        Enum(AIInteractionType),
        nullable=False,
        index=True,
    )
    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    response: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    tokens_used: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    lead: Mapped["Lead"] = relationship(
        back_populates="ai_interactions"
    )