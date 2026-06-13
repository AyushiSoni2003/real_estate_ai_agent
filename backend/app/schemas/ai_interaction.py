from uuid import UUID
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class AIInteractionCreate(BaseModel):
    lead_id: UUID
    interaction_type: Literal[
        "follow_up_message",
        "property_recommendation",
        "lead_summary",
        "appointment_assistant",
    ]
    prompt: str
    response: str
    model: str
    tokens_used: int | None = None


class AIInteractionResponse(BaseModel):
    id: UUID
    lead_id: UUID
    interaction_type: Literal[
        "follow_up_message",
        "property_recommendation",
        "lead_summary",
        "appointment_assistant",
    ]
    prompt: str
    response: str
    model: str
    tokens_used: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
