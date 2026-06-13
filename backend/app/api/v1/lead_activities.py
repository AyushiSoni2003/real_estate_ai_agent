"""Lead Activities API endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.lead_activity import LeadActivity
from app.schemas.lead_activity import LeadActivityResponse

router = APIRouter(prefix="/leads", tags=["lead-activities"])


@router.get("/{lead_id}/activities", response_model=list[LeadActivityResponse])
async def get_lead_activities(
    lead_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    event_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get activity timeline for a lead with optional filtering."""
    query = select(LeadActivity).where(LeadActivity.lead_id == lead_id)
    
    if event_type:
        query = query.where(LeadActivity.event_type == event_type)
    
    query = query.order_by(LeadActivity.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{lead_id}/activities/summary")
async def get_lead_activity_summary(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get summary of activities for a lead (counts by event type)."""
    from sqlalchemy import func
    
    result = await db.execute(
        select(
            LeadActivity.event_type,
            func.count(LeadActivity.id).label("count")
        )
        .where(LeadActivity.lead_id == lead_id)
        .group_by(LeadActivity.event_type)
    )
    
    summary = {}
    for event_type, count in result.all():
        summary[event_type] = count
    
    return {
        "lead_id": lead_id,
        "activity_summary": summary,
        "total_activities": sum(summary.values())
    }
