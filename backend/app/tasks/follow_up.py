"""Celery follow-up tasks."""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID
from celery import Task
from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.lead import Lead
from app.models.follow_up_log import FollowUpLog, FollowUpDay, FollowUpStatus
from app.agents.conversation import run_follow_up_agent
from app.services.messaging import send_message

FOLLOW_UP_DAYS = [1, 3, 7, 30]

def schedule_follow_ups_for_lead(lead_id: str, created_at: datetime):
    """
    Call this immediately after a lead is created.
    Schedules all four follow-up tasks with their ETAs.
    """
    for day in FOLLOW_UP_DAYS:
        eta = created_at + timedelta(days=day)
        send_follow_up.apply_async(
            args=[lead_id, day],
            eta=eta,
            task_id=f"followup-{lead_id}-day{day}",
        )

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    name="tasks.send_follow_up",
)
def send_follow_up(self: Task, lead_id: str, follow_up_day: int):
    """
    Main follow-up task. Runs inside Celery worker process.
    Uses asyncio.run() to call async DB and agent code.
    """
    try:
        asyncio.run(_async_send_follow_up(lead_id, follow_up_day))
    except Exception as exc:
        raise self.retry(exc=exc)

async def _async_send_follow_up(lead_id: str, follow_up_day: int):
    async with AsyncSessionLocal() as db:
        lead = await db.get(Lead, UUID(lead_id))
        if not lead:
            return
        if lead.status in ("converted", "lost"):
            return

        log = FollowUpLog(
            lead_id=lead.id,
            follow_up_day=FollowUpDay(follow_up_day),
            status=FollowUpStatus.SCHEDULED,
            scheduled_at=datetime.now(timezone.utc),
        )
        db.add(log)
        await db.flush()

        try:
            result = await run_follow_up_agent(lead, follow_up_day, db)
            await send_message(
                lead=lead,
                message_body=result["message"],
                channel=result["channel"],
                db=db,
            )
            log.status = FollowUpStatus.SENT
            log.sent_at = datetime.now(timezone.utc)
        except Exception as e:
            log.status = FollowUpStatus.FAILED
            log.error_message = str(e)
            raise

        await db.commit()