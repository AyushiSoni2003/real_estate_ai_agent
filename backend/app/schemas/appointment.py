from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.appointment import AppointmentStatus

class AppointmentCreate(BaseModel):
    lead_id: UUID
    property_id: UUID | None = None
    scheduled_at: datetime
    notes: str | None = None

class AppointmentUpdate(BaseModel):
    status: AppointmentStatus | None = None
    scheduled_at: datetime | None = None
    notes: str | None = None

class AppointmentResponse(BaseModel):
    id: UUID
    lead_id: UUID
    agent_id: UUID
    property_id: UUID | None
    scheduled_at: datetime
    status: AppointmentStatus
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
