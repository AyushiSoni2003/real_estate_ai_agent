from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from app.agents.appointment_state import AppointmentAgentState, TimeSlot
from app.models.agent_availability import AgentAvailability
from app.core.config import settings

llm = ChatOpenAI(
    model="gpt-4o",
    api_key=settings.OPENAI_API_KEY,
    temperature=0.4,
)

async def fetch_slots_node(
    state: AppointmentAgentState,
    db: AsyncSession,
) -> AppointmentAgentState:
    """
    Reads up to 3 available (not booked) future slots
    for the agent. Returns them in the state for the
    next node to offer to the lead.
    """
    from uuid import UUID
    result = await db.execute(
        select(AgentAvailability)
        .where(AgentAvailability.agent_id == UUID(state["agent_id"]))
        .where(AgentAvailability.is_booked == False)
        .where(AgentAvailability.start_time > datetime.now(timezone.utc))
        .order_by(AgentAvailability.start_time)
        .limit(3)
    )
    slots = result.scalars().all()

    available: list[TimeSlot] = [
        {
            "start": s.start_time,
            "end": s.end_time,
            "slot_label": s.start_time.strftime("%A, %d %b at %I:%M %p"),
        }
        for s in slots
    ]

    if not available:
        return {**state, "status": "error", "error": "No available slots"}

    return {**state, "available_slots": available}

async def propose_slots_node(
    state: AppointmentAgentState,
) -> AppointmentAgentState:
    """
    GPT-4o writes a friendly message presenting the
    available slots as numbered options. The message
    is natural — not a formatted list of times.
    """
    slots = state["available_slots"]
    round_num = state["negotiation_round"]
    last_msg = state.get("last_lead_message", "")

    slot_text = "\n".join([f"{i+1}. {s['slot_label']}" for i, s in enumerate(slots)])

    if round_num == 0:
        context = "This is the first time we're offering slots."
    else:
        context = (
            f"The lead previously said: '{last_msg}'. "
            "They weren't happy with the previous slots — offer new ones warmly."
        )

    system = (
        "You are a professional real estate assistant. "
        "Write short, warm, conversational messages. "
        "Never sound like an automated system. "
        "Present slot options naturally, not as a rigid form."
    )
    user = (f"{context}"f"Available slots:{slot_text}"
        "Write a message asking the lead which slot works for them. "
        "Keep it under 80 words. Don't use bullet points."
    )

    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=user),
    ])

    return {
        **state,
        "agent_message": response.content,
        "offered_slots": slots,
        "negotiation_round": round_num + 1,
    }

async def parse_reply_node(
    state: AppointmentAgentState,
) -> AppointmentAgentState:
    """
    Reads the lead's reply and determines intent:
      - accepted: lead picked a slot (extract which one)
      - new_slots: lead wants different options
      - declined: lead no longer interested
      - unclear: couldn't parse, ask again
    Uses GPT-4o to handle natural language replies like
    'the second one works' or 'can we do something later?'
    """
    reply = state["last_lead_message"]
    offered = state["offered_slots"]

    slot_context = "\n".join([
        f"{i+1}. {s['slot_label']}"
        for i, s in enumerate(offered)
    ])

    system = (
        "You extract appointment intent from a lead's reply. "
        "Return ONLY valid JSON. No explanation, no markdown."
    )
    user = (
        f"Offered slots:{slot_context}"
        f"Lead's reply: '{reply}'"
        "Return JSON: "
        '{"intent": "accepted"|"new_slots"|"declined"|"unclear", '
        '"slot_index": 0|1|2|null}'
    )

    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=user),
    ])

    import json
    try:
        parsed = json.loads(response.content)
        intent = parsed.get("intent", "unclear")
        slot_index = parsed.get("slot_index")
    except (json.JSONDecodeError, KeyError):
        intent = "unclear"
        slot_index = None

    if intent == "accepted" and slot_index is not None:
        selected = offered[slot_index]
        return {**state, "status": "negotiating",
                "selected_slot": selected, "_intent": "accepted"}
    elif intent == "declined":
        return {**state, "status": "declined"}
    elif intent == "new_slots":
        return {**state, "_intent": "new_slots"}
    else:
        return {**state, "_intent": "unclear"}

async def confirm_booking_node(
    state: AppointmentAgentState,
    db: AsyncSession,
) -> AppointmentAgentState:
    """
    Writes the confirmed appointment to the DB,
    marks the agent's availability slot as booked,
    and triggers the Google Calendar event creation.
    """
    from uuid import UUID
    from app.models.appointment import Appointment, AppointmentStatus
    from app.models.lead import Lead, LeadStatus
    from app.services.calendar_service import create_calendar_event

    slot = state["selected_slot"]

    appointment = Appointment(
        lead_id=UUID(state["lead_id"]),
        agent_id=UUID(state["agent_id"]),
        property_id=UUID(state["property_id"]) if state["property_id"] else None,
        scheduled_at=slot["start"],
        status=AppointmentStatus.CONFIRMED,
        notes=f"Booked via AI agent. Slot: {slot['slot_label']}",
    )
    db.add(appointment)

    result = await db.execute(
        select(AgentAvailability)
        .where(AgentAvailability.agent_id == UUID(state["agent_id"]))
        .where(AgentAvailability.start_time == slot["start"])
    )
    avail = result.scalar_one_or_none()
    if avail:
        avail.is_booked = True

    lead = await db.get(Lead, UUID(state["lead_id"]))
    if lead:
        lead.status = LeadStatus.APPOINTMENT_SET

    await db.flush()

    try:
        event_id = await create_calendar_event(
            agent_id=state["agent_id"],
            appointment=appointment,
            lead_name=lead.full_name if lead else "Lead",
            slot=slot,
        )
        appointment.google_event_id = event_id
    except Exception:
        pass

    await db.commit()

    return {
        **state,
        "status": "confirmed",
        "agent_message": (
            f"You're all set! Your visit is confirmed for "
            f"{slot['slot_label']}. We'll send you a reminder "
            f"24 hours before. See you then!"
        ),
    }
