from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from typing import Literal


class MessageCreate(BaseModel):
    lead_id: UUID
    channel: Literal["whatsapp", "email", "sms"]
    direction: Literal["outbound", "inbound"] | None = "outbound"
    body: str
    external_id: str | None = None


class MessageResponse(BaseModel):
    id: UUID
    lead_id: UUID
    channel: Literal["whatsapp", "email", "sms"]
    direction: Literal["outbound", "inbound"]
    status: Literal["sent", "delivered", "read", "failed"]
    body: str
    external_id: str | None
    sent_at: datetime
    delivered_at: datetime | None
    read_at: datetime | None

    model_config = {"from_attributes": True}
