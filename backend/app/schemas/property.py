from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class PropertyCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    address: str = Field(..., min_length=5)
    city: str
    price: int = Field(..., gt=0)
    bedrooms: int | None = Field(None, ge=0)
    bathrooms: int | None = Field(None, ge=0)
    area_sqft: int | None = Field(None, gt=0)
    latitude: float | None = None
    longitude: float | None = None
    image_urls: list[str] | None = None

class PropertyResponse(BaseModel):
    id: UUID
    agent_id: UUID
    title: str
    description: str | None
    address: str
    city: str
    price: int
    bedrooms: int | None
    bathrooms: int | None
    area_sqft: int | None
    latitude: float | None
    longitude: float | None
    is_available: bool
    created_at: datetime

    model_config = {"from_attributes": True}
