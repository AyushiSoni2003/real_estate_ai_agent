from datetime import datetime
from typing import Literal, TypedDict


class TimeSlot(TypedDict):
    start: datetime
    end: datetime
    slot_label: str


class AppointmentAgentState(TypedDict):
    lead_id: str
    agent_id: str
    property_id: str | None
    conversation_id: str
    available_slots: list[TimeSlot]
    offered_slots: list[TimeSlot]
    selected_slot: TimeSlot | None
    negotiation_round: int
    max_rounds: int
    last_lead_message: str
    agent_message: str
    status: Literal[
        "negotiating",
        "confirmed",
        "declined",
        "max_rounds_exceeded",
        "error",
    ]
    google_event_id: str | None
    error: str | None
    intent: Literal["accepted", "new_slots", "unclear"]
    _is_resume: bool
