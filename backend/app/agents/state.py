from typing import TypedDict, Literal
from app.models.lead import Lead

class AgentState(TypedDict):
    lead: Lead
    follow_up_day: int
    lead_summary: str
    matching_properties: list[dict]
    message: str
    channel: Literal["whatsapp", "email", "sms"]
    error: str | None