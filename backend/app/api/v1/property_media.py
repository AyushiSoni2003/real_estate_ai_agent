"""Property Media API endpoints."""
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.property_media import PropertyMedia
from app.models.agent import Agent
from app.schemas.property_media import PropertyMediaCreate, PropertyMediaResponse

router = APIRouter(prefix="/properties", tags=["property-media"])


@router.post("/{property_id}/media", response_model=PropertyMediaResponse, status_code=201)
async def upload_media(
    property_id: UUID,
    data: PropertyMediaCreate,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload media (image/video/floor plan) for a property."""
    # Verify property belongs to agent
    from app.models.property import Property
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if prop.agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload media for this property")
    
    media = PropertyMedia(
        id=uuid4(),
        property_id=property_id,
        url=str(data.url),
        media_type=data.media_type
    )
    db.add(media)
    await db.flush()
    await db.refresh(media)
    return media


@router.get("/{property_id}/media", response_model=list[PropertyMediaResponse])
async def list_property_media(
    property_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List all media for a property."""
    result = await db.execute(
        select(PropertyMedia)
        .where(PropertyMedia.property_id == property_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{property_id}/media/{media_id}", response_model=PropertyMediaResponse)
async def get_media(
    property_id: UUID,
    media_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get specific media details."""
    media = await db.get(PropertyMedia, media_id)
    if not media or media.property_id != property_id:
        raise HTTPException(status_code=404, detail="Media not found")
    return media


@router.delete("/{property_id}/media/{media_id}", status_code=204)
async def delete_media(
    property_id: UUID,
    media_id: UUID,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete media from a property."""
    from app.models.property import Property
    
    media = await db.get(PropertyMedia, media_id)
    if not media or media.property_id != property_id:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Verify property belongs to agent
    prop = await db.get(Property, property_id)
    if prop.agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.delete(media)
    await db.flush()
