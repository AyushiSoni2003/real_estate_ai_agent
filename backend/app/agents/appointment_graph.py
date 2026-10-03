import json
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from app.agents.appointment_state import AppointmentAgentState
from app.agents.appointment_nodes import (
    fetch_slots_node,
    propose_slots_node,
    parse_reply_node,
    confirm_booking_node,
)

def route_after_reply(state: AppointmentAgentState) -> str:
    """
    Conditional edge function. LangGraph calls this after
    parse_reply_node and routes to the correct next node.
    """
    if state.get("status") == "declined":
        return "end_declined"

    intent = state.get("_intent", "unclear")

    if intent == "accepted" and state.get("selected_slot"):
        return "confirm_booking"

    if state.get("negotiation_round", 0) >= state.get("max_rounds", 3):
        return "end_max_rounds"

    elif intent == "new_slots":
        return "fetch_slots"
    else:
        return "propose_slots"


def route_start(state: AppointmentAgentState) -> str:
    """Send new conversations to slot lookup and resumed ones to reply parsing."""
    return "parse_reply" if state.get("_is_resume") else "fetch_slots"


def route_after_fetch(state: AppointmentAgentState) -> str:
    """Stop cleanly if no slots were found; otherwise offer them."""
    return "end_no_slots" if state.get("status") == "error" else "propose_slots"


def mark_max_rounds_exceeded(state: AppointmentAgentState) -> AppointmentAgentState:
    return {
        **state,
        "status": "max_rounds_exceeded",
        "agent_message": "I couldn't find a time that works after a few tries. Please contact the agent and they can help schedule a visit.",
    }

def build_appointment_graph():
    graph = StateGraph(AppointmentAgentState)

    async def fetch_slots_with_db(
        state: AppointmentAgentState, config: RunnableConfig
    ) -> AppointmentAgentState:
        db = config["configurable"]["db"]
        return await fetch_slots_node(state, db)

    async def confirm_booking_with_db(
        state: AppointmentAgentState, config: RunnableConfig
    ) -> AppointmentAgentState:
        db = config["configurable"]["db"]
        return await confirm_booking_node(state, db)

    graph.add_node("fetch_slots", fetch_slots_with_db)
    graph.add_node("propose_slots", propose_slots_node)
    graph.add_node("parse_reply", parse_reply_node)
    graph.add_node("confirm_booking", confirm_booking_with_db)
    graph.add_node("route_start", lambda state: state)
    graph.add_node("mark_max_rounds_exceeded", mark_max_rounds_exceeded)

    graph.set_entry_point("route_start")
    graph.add_conditional_edges(
        "route_start",
        route_start,
        {"fetch_slots": "fetch_slots", "parse_reply": "parse_reply"},
    )
    graph.add_conditional_edges(
        "fetch_slots",
        route_after_fetch,
        {"propose_slots": "propose_slots", "end_no_slots": END},
    )
    graph.add_edge("propose_slots", END)

    graph.add_conditional_edges(
        "parse_reply",
        route_after_reply,
        {
            "confirm_booking": "confirm_booking",
            "fetch_slots": "fetch_slots",
            "propose_slots": "propose_slots",
            "end_declined": END,
            "end_max_rounds": "mark_max_rounds_exceeded",
        },
    )
    graph.add_edge("confirm_booking", END)
    graph.add_edge("mark_max_rounds_exceeded", END)

    return graph.compile()

appointment_graph = build_appointment_graph()


def _encode_json_value(value):
    """Encode datetimes anywhere in the graph state as marked JSON objects."""
    if isinstance(value, datetime):
        return {
            "__realtyiq_type__": "datetime",
            "value": value.isoformat(),
        }
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _decode_json_value(value: dict):
    """Restore datetime values encoded by ``_encode_json_value``."""
    if (
        value.get("__realtyiq_type__") == "datetime"
        and set(value) == {"__realtyiq_type__", "value"}
    ):
        return datetime.fromisoformat(value["value"])
    return value

async def start_appointment_flow(
    lead_id: str,
    agent_id: str,
    property_id: str | None,
    db: AsyncSession,
) -> dict:
    """
    Called when a lead first expresses interest.
    Runs fetch_slots → propose_slots, then pauses.
    Persists state to DB for the next webhook turn.
    """
    initial_state: AppointmentAgentState = {
        "lead_id": lead_id,
        "agent_id": agent_id,
        "property_id": property_id,
        "conversation_id": str(uuid4()),
        "available_slots": [],
        "offered_slots": [],
        "selected_slot": None,
        "negotiation_round": 0,
        "max_rounds": 3,
        "last_lead_message": "",
        "agent_message": "",
        "status": "negotiating",
        "google_event_id": None,
        "error": None,
    }

    final_state = await appointment_graph.ainvoke(
        initial_state,
        config={"configurable": {"db": db}},
    )

    await _persist_state(lead_id, final_state, db)
    return final_state

async def resume_appointment_flow(
    lead_id: str,
    lead_reply: str,
    db: AsyncSession,
) -> dict:
    """
    Called when a lead replies to a slot proposal.
    Loads persisted state, injects the reply, resumes
    graph from parse_reply node.
    """
    state = await _load_state(lead_id, db)
    if not state:
        return {"status": "error", "error": "No active negotiation"}

    state["last_lead_message"] = lead_reply
    state["_is_resume"] = True

    final_state = await appointment_graph.ainvoke(
        state,
        config={"configurable": {"db": db}},
    )

    await _persist_state(lead_id, final_state, db)
    return final_state

async def _persist_state(lead_id: str, state: dict, db: AsyncSession):
    from uuid import UUID
    from app.models.conversation_state import ConversationState
    from sqlalchemy import select

    result = await db.execute(
        select(ConversationState).where(
            ConversationState.lead_id == UUID(lead_id)
        )
    )
    existing = result.scalar_one_or_none()

    serialized_state = json.dumps(state, default=_encode_json_value)

    if existing:
        existing.graph_state = serialized_state
        existing.status = state.get("status", "negotiating")
    else:
        db.add(ConversationState(
            lead_id=UUID(lead_id),
            graph_state=serialized_state,
            status=state.get("status", "negotiating"),
        ))
    await db.flush()

async def _load_state(lead_id: str, db: AsyncSession) -> dict | None:
    from uuid import UUID
    from app.models.conversation_state import ConversationState
    from sqlalchemy import select

    result = await db.execute(
        select(ConversationState).where(
            ConversationState.lead_id == UUID(lead_id)
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        return None
    return json.loads(record.graph_state, object_hook=_decode_json_value)
