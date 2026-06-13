import uuid
import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lead import Lead

class FollowUpDay(int, enum.Enum):
    DAY_1  = 1
    DAY_3  = 3
    DAY_7  = 7
    DAY_30 = 30

class FollowUpStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    SENT      = "sent"
    FAILED    = "failed"
    SKIPPED   = "skipped"

class FollowUpLog(Base):
    __tablename__ = "follow_up_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )
    follow_up_day: Mapped[FollowUpDay] = mapped_column(
        Enum(FollowUpDay), nullable=False
    )
    status: Mapped[FollowUpStatus] = mapped_column(
        Enum(FollowUpStatus), default=FollowUpStatus.SCHEDULED
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    lead: Mapped["Lead"] = relationship(back_populates="follow_up_logs")
