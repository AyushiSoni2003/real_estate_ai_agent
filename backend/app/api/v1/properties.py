"""Properties API endpoints."""
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.property import Property
from app.models.agent import Agent
from app.schemas.property import PropertyCreate, PropertyResponse
from app.schemas.search import PropertySearchParams, Pagination, PaginatedResponse

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("/", response_model=PropertyResponse, status_code=201)
async def create_property(
    data: PropertyCreate,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new property listing."""
    prop = Property(
        id=uuid4(),
        agent_id=current_user.id,
        **data.model_dump()
    )
    db.add(prop)
    await db.flush()
    await db.refresh(prop)
    return prop


@router.get("/", response_model=list[PropertyResponse])
async def list_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all properties with pagination."""
    result = await db.execute(
        select(Property).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/search", response_model=list[PropertyResponse])
async def search_properties(
    params: PropertySearchParams = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Advanced search for properties with filters."""
    query = select(Property)
    filters = []
    
    if params.city:
        filters.append(Property.city == params.city)
    if params.price_min is not None:
        filters.append(Property.price >= params.price_min)
    if params.price_max is not None:
        filters.append(Property.price <= params.price_max)
    if params.bedrooms is not None:
        filters.append(Property.bedrooms == params.bedrooms)
    if params.bathrooms is not None:
        filters.append(Property.bathrooms == params.bathrooms)
    if params.area_sqft_min is not None:
        filters.append(Property.area_sqft >= params.area_sqft_min)
    if params.area_sqft_max is not None:
        filters.append(Property.area_sqft <= params.area_sqft_max)
    if params.is_available is not None:
        filters.append(Property.is_available == params.is_available)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get property details by ID."""
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@router.patch("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: UUID,
    data: dict,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update property details."""
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    
    if prop.agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this property")
    
    for key, value in data.items():
        if value is not None:
            setattr(prop, key, value)
    
    await db.flush()
    await db.refresh(prop)
    return prop


@router.delete("/{property_id}", status_code=204)
async def delete_property(
    property_id: UUID,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a property."""
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    
    if prop.agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this property")
    
    await db.delete(prop)
    await db.flush()


@router.get("/{property_id}/available")
async def check_property_available(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Check if property is available."""
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return {"property_id": property_id, "is_available": prop.is_available}
