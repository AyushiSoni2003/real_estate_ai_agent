from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional
from uuid import UUID
from app.schemas.property import PropertyResponse


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    radius_km: float = Field(10.0, ge=1.0, le=100.0)
    top_k: int = Field(5, ge=1, le=20)


class PropertySearchResult(BaseModel):
    id: UUID
    title: str
    address: str
    city: str
    price: int
    bedrooms: int | None
    bathrooms: int | None
    area_sqft: int | None
    latitude: float | None
    longitude: float | None
    is_available: bool
    similarity_score: float
    image_urls: list[str] | None

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    query: str
    results: list[PropertySearchResult]
    total: int


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


class SemanticPropertyResult(BaseModel):
    property: PropertyResponse
    similarity_score: float
