from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.agent import Agent
from app.models.agent_availability import AgentAvailability
from app.models.appointment import Appointment, AppointmentStatus
from app.models.lead import Lead, LeadStatus


async def make_lead_and_availability(db_session, slot_count=6):
    agent_id = uuid4()
    lead_id = uuid4()
    agent = Agent(
        id=agent_id,
        email=f"agent-{agent_id}@example.com",
        hashed_password="not-a-real-password-hash",
        full_name="Test Agent",
    )
    lead = Lead(id=lead_id, agent_id=agent_id, full_name="Test Lead")
    first_start = datetime.now(timezone.utc) + timedelta(days=2)
    slots = []
    for index in range(slot_count):
        start = first_start + timedelta(hours=index * 3)
        slot = AgentAvailability(
            id=uuid4(),
            agent_id=agent_id,
            start_time=start,
            end_time=start + timedelta(hours=1),
            is_booked=False,
        )
        slots.append(slot)
    db_session.add_all([agent, lead, *slots])
    await db_session.flush()
    return agent, lead, slots


@pytest.mark.asyncio
async def test_lead_picks_offered_slot_and_booking_is_confirmed(
    db_session, appointment_flow
):
    graph_module, nodes = appointment_flow
    agent, lead, slots = await make_lead_and_availability(db_session, slot_count=3)
    nodes.llm.ainvoke.side_effect = [
        SimpleNamespace(content="Would one of these visit times work for you?"),
        SimpleNamespace(content='{"intent":"accepted","slot_index":1}'),
    ]

    offer = await graph_module.start_appointment_flow(
        str(lead.id), str(agent.id), None, db_session
    )
    assert offer["status"] == "negotiating"
    assert len(offer["offered_slots"]) == 3
    assert isinstance(offer["offered_slots"][1]["start"], datetime)

    result = await graph_module.resume_appointment_flow(
        str(lead.id), "The second time works for me", db_session
    )

    assert result["status"] == "confirmed"
    assert "confirmed" in result["agent_message"].lower()
    appointment_id = (await db_session.execute(select(Appointment.id))).scalar_one()
    appointment = await db_session.get(Appointment, appointment_id)
    assert appointment.status == AppointmentStatus.CONFIRMED
    assert appointment.scheduled_at == slots[1].start_time
    assert appointment.google_event_id == "mock-calendar-event"
    await db_session.refresh(lead)
    await db_session.refresh(slots[1])
    assert lead.status == LeadStatus.APPOINTMENT_SET
    assert slots[1].is_booked is True


@pytest.mark.asyncio
async def test_different_times_offers_new_slots_then_unclear_reply_repeats_them(
    db_session, appointment_flow
):
    graph_module, nodes = appointment_flow
    agent, lead, _ = await make_lead_and_availability(db_session, slot_count=6)
    nodes.llm.ainvoke.side_effect = [
        SimpleNamespace(content="Here are a few visit times."),
        SimpleNamespace(content='{"intent":"new_slots","slot_index":null}'),
        SimpleNamespace(content="Here are some other times."),
        SimpleNamespace(content='{"intent":"unclear","slot_index":null}'),
        SimpleNamespace(content="Could you tell me which of these works best?"),
    ]

    first_offer = await graph_module.start_appointment_flow(
        str(lead.id), str(agent.id), None, db_session
    )
    second_offer = await graph_module.resume_appointment_flow(
        str(lead.id), "Could you suggest different times?", db_session
    )
    clarification = await graph_module.resume_appointment_flow(
        str(lead.id), "I'm not sure", db_session
    )

    first_times = {slot["start"] for slot in first_offer["offered_slots"]}
    second_times = {slot["start"] for slot in second_offer["offered_slots"]}
    clarification_times = {slot["start"] for slot in clarification["offered_slots"]}
    assert first_times.isdisjoint(second_times)
    assert second_times == clarification_times
    assert clarification["status"] == "negotiating"
    assert "which of these" in clarification["agent_message"].lower()
