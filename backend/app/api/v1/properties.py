"""Properties API endpoints."""
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from geoalchemy2.elements import WKTElement
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.property import Property
from app.models.agent import Agent
from app.schemas.property import PropertyCreate, PropertyResponse
from app.schemas.search import PropertySearchParams, Pagination, PaginatedResponse
from app.services.property_embedder import embed_and_index_property

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("/", response_model=PropertyResponse, status_code=201)
async def create_property(
    data: PropertyCreate,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new property listing."""
    prop_data = data.model_dump()
    if data.latitude is not None and data.longitude is not None:
        prop_data["location"] = WKTElement(
            f"POINT({data.longitude} {data.latitude})",
            srid=4326,
        )

    prop = Property(
        id=uuid4(),
        agent_id=current_user.id,
        **prop_data,
    )
    db.add(prop)
    await db.flush()
    await db.refresh(prop)
    await embed_and_index_property(prop)
    prop.qdrant_indexed = True
    await db.commit()
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

    allowed_fields = {
        "title", "description", "address", "city", "price", "bedrooms",
        "bathrooms", "area_sqft", "latitude", "longitude", "amenities",
        "image_urls", "is_available",
    }
    unknown_fields = data.keys() - allowed_fields
    if unknown_fields:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported property fields: {', '.join(sorted(unknown_fields))}",
        )

    clearable_fields = {
        "description", "bedrooms", "bathrooms", "area_sqft", "latitude",
        "longitude", "amenities", "image_urls",
    }
    changed_fields: set[str] = set()
    for key, value in data.items():
        if value is None and key not in clearable_fields:
            continue
        if getattr(prop, key) != value:
            setattr(prop, key, value)
            changed_fields.add(key)

    if changed_fields & {"latitude", "longitude"}:
        if prop.latitude is not None and prop.longitude is not None:
            prop.location = WKTElement(
                f"POINT({prop.longitude} {prop.latitude})",
                srid=4326,
            )
        else:
            prop.location = None
    
    await db.flush()
    await db.refresh(prop)
    embedding_fields = {
        "title", "description", "address", "city", "price", "bedrooms",
        "bathrooms", "area_sqft", "amenities", "latitude", "longitude",
        "is_available",
    }
    if changed_fields & embedding_fields:
        await embed_and_index_property(prop)
        prop.qdrant_indexed = True
    await db.commit()
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
