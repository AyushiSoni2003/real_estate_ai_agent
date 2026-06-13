"""Property SQLAlchemy model."""
import uuid
from datetime import datetime
from sqlalchemy import (
DateTime, ForeignKey, String, Text, Integer, Float, Boolean, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.appointment import Appointment
from app.models.agent import Agent
from app.models.property_media import PropertyMedia
 

class Property(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), index=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    bedrooms: Mapped[int | None] = mapped_column(Integer)
    bathrooms: Mapped[int | None] = mapped_column(Integer)
    area_sqft: Mapped[int | None] = mapped_column(Integer)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


    agent: Mapped["Agent"] = relationship(back_populates="properties")
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="property"
    )
    media_files: Mapped[list["PropertyMedia"]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan"
    )
