from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.lead import Lead
from app.tasks.follow_up import send_follow_up

router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])

@router.post("/trigger/{lead_id}/{day}")
async def trigger_follow_up(
    lead_id: UUID,
    day: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger a follow-up for testing.
    day must be 1, 3, 7, or 30.
    """
    if day not in [1, 3, 7, 30]:
        raise HTTPException(
            status_code=400,
            detail="day must be 1, 3, 7, or 30"
        )
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    task = send_follow_up.delay(str(lead_id), day)
    return {
        "task_id": task.id,
        "status": "queued",
        "lead_id": str(lead_id),
        "follow_up_day": day,
    }

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Check whether a Celery task has completed.
    """
    from app.tasks.celery_app import celery_app
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": str(result.result) if result.ready() else None,
    }
