"""Agent SQLAlchemy model."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Enum, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.lead import Lead
    from app.models.property import Property
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"

class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.AGENT,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    leads: Mapped[list["Lead"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    properties: Mapped[list["Property"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
