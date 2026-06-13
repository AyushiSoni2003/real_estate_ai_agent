from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Literal


class AgentCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: str | None = None
    role: Literal["agent", "admin"] | None = None


class AgentUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    role: Literal["agent", "admin"] | None = None


class AgentResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    phone: str | None
    role: Literal["agent", "admin"]
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
