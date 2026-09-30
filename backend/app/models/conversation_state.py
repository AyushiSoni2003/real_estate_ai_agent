import uuid
from datetime import datetime
from sqlalchemy import DateTime, Text, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class ConversationState(Base):
    """
    Persists LangGraph state between webhook calls.
    One row per active appointment negotiation.
    """
    __tablename__ = "conversation_states"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        index=True, unique=True
    )
    graph_state: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="negotiating")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
