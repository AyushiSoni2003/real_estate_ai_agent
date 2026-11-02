"""Semantic property search API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.agent import Agent
from app.schemas.search import (
    PropertySearchResult,
    SearchRequest,
    SearchResponse,
)
from app.services.search import semantic_property_search


router = APIRouter(prefix="/search", tags=["search"])


@router.post("/properties", response_model=SearchResponse)
async def search_properties(
    request: SearchRequest,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Find the authenticated agent's available properties by meaning/location."""
    matches = await semantic_property_search(
        query=request.query,
        db=db,
        agent_id=str(current_user.id),
        radius_km=request.radius_km,
        top_k=request.top_k,
    )

    results = [
        PropertySearchResult(
            id=match["property"].id,
            title=match["property"].title,
            address=match["property"].address,
            city=match["property"].city,
            price=match["property"].price,
            bedrooms=match["property"].bedrooms,
            bathrooms=match["property"].bathrooms,
            area_sqft=match["property"].area_sqft,
            latitude=match["property"].latitude,
            longitude=match["property"].longitude,
            is_available=match["property"].is_available,
            image_urls=match["property"].image_urls,
            similarity_score=match["similarity_score"],
        )
        for match in matches
    ]
    return SearchResponse(
        query=request.query,
        results=results,
        total=len(results),
    )
