from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional


class PropertySearchParams(BaseModel):
    city: str | None = None
    price_min: int | None = Field(None, ge=0)
    price_max: int | None = Field(None, ge=0)
    bedrooms: int | None = Field(None, ge=0)
    bathrooms: int | None = Field(None, ge=0)
    area_sqft_min: int | None = Field(None, gt=0)
    area_sqft_max: int | None = Field(None, gt=0)
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float | None = Field(None, gt=0)
    is_available: bool | None = None


class Pagination(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    total: int = Field(0, ge=0)
    total_pages: int = Field(0, ge=0)


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    pagination: Pagination
