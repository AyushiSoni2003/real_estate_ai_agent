from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import BaseModel
from typing import Literal


class LeadActivityResponse(BaseModel):
    id: UUID
    lead_id: UUID
    event_type: Literal[
        "lead_created",
        "message_sent",
        "message_delivered",
        "message_read",
        "message_replied",
        "property_viewed",
        "appointment_booked",
        "appointment_completed",
        "appointment_cancelled",
        "ai_recommendation_generated",
    ]
    event_data: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
