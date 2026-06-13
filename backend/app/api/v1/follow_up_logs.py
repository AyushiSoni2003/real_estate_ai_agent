"""Follow-Up Logs API endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.follow_up_log import FollowUpLog
from app.models.agent import Agent
from app.schemas.follow_up_log import FollowUpLogResponse

router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])


@router.get("/leads/{lead_id}/follow-ups", response_model=list[FollowUpLogResponse])
async def get_lead_follow_ups(
    lead_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get follow-up schedule for a lead."""
    result = await db.execute(
        select(FollowUpLog)
        .where(FollowUpLog.lead_id == lead_id)
        .order_by(FollowUpLog.scheduled_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.patch("/{log_id}", response_model=FollowUpLogResponse)
async def update_follow_up_status(
    log_id: UUID,
    status: str = Query(..., description="Status: scheduled, sent, failed, skipped"),
    db: AsyncSession = Depends(get_db),
):
    """Mark follow-up as sent, failed, or skipped."""
    log = await db.get(FollowUpLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Follow-up log not found")
    
    if status not in ["scheduled", "sent", "failed", "skipped"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    log.status = status
    if status == "sent":
        log.sent_at = datetime.utcnow()
    
    await db.flush()
    await db.refresh(log)
    return log


@router.get("/pending")
async def get_pending_follow_ups(
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pending follow-ups for current agent."""
    from app.models.lead import Lead
    
    result = await db.execute(
        select(FollowUpLog)
        .join(Lead)
        .where(
            (Lead.agent_id == current_user.id) &
            (FollowUpLog.status == "scheduled") &
            (FollowUpLog.scheduled_at <= datetime.utcnow())
        )
        .order_by(FollowUpLog.scheduled_at.asc())
    )
    return result.scalars().all()
