from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models.lead import LeadStatus

class LeadCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr | None = None
    phone: str | None = None
    source: str | None = None
    budget_min: int | None = Field(None, ge=0)
    budget_max: int | None = Field(None, ge=0)
    preferred_location: str | None = None
    notes: str | None = None

class LeadUpdate(BaseModel):
    full_name: str | None = None
    status: LeadStatus | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    preferred_location: str | None = None
    notes: str | None = None

class LeadResponse(BaseModel):
    id: UUID
    agent_id: UUID
    full_name: str
    email: str | None
    phone: str | None
    status: LeadStatus
    budget_min: int | None
    budget_max: int | None
    preferred_location: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

# Why model_config from_attributes=True? 
# This tells Pydantic to read data from SQLAlchemy object attributes, 
# not just dicts. Without it, LeadResponse(lead_object) silently returns empty fields.
