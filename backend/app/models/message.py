import uuid
import enum
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lead import Lead

class MessageChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL    = "email"
    SMS      = "sms"

class MessageDirection(str, enum.Enum):
    OUTBOUND = "outbound"
    INBOUND  = "inbound"

class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[MessageChannel] = mapped_column(
        Enum(MessageChannel), nullable=False, index=True
    )
    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection), default=MessageDirection.OUTBOUND
    )
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus),
        default=MessageStatus.SENT,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255))
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    lead: Mapped["Lead"] = relationship(back_populates="messages")
