from uuid import UUID
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class FollowUpLogCreate(BaseModel):
    lead_id: UUID
    follow_up_day: Literal[1, 3, 7, 30]
    scheduled_at: datetime


class FollowUpLogResponse(BaseModel):
    id: UUID
    lead_id: UUID
    follow_up_day: Literal[1, 3, 7, 30]
    status: Literal["scheduled", "sent", "failed", "skipped"]
    scheduled_at: datetime
    sent_at: datetime | None
    error_message: str | None

    model_config = {"from_attributes": True}
