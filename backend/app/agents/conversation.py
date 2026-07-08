"""LangGraph conversation agent."""
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.state import AgentState
from app.agents.nodes import (
    qualify_lead_node,
    match_properties_node,
    generate_message_node,
    route_channel_node,
)
from app.models.lead import Lead

def build_follow_up_graph():
    graph = StateGraph(AgentState)

    graph.add_node("qualify", qualify_lead_node)
    graph.add_node("match_properties", match_properties_node)
    graph.add_node("generate_message", generate_message_node)
    graph.add_node("route_channel", route_channel_node)

    graph.set_entry_point("qualify")
    graph.add_edge("qualify", "match_properties")
    graph.add_edge("match_properties", "generate_message")
    graph.add_edge("generate_message", "route_channel")
    graph.add_edge("route_channel", END)

    return graph.compile()

follow_up_graph = build_follow_up_graph()

async def run_follow_up_agent(
    lead: Lead,
    follow_up_day: int,
    db: AsyncSession,
) -> dict:
    """
    Runs the LangGraph pipeline for one lead.
    Returns {"message": str, "channel": str}.
    """
    initial_state: AgentState = {
        "lead": lead,
        "follow_up_day": follow_up_day,
        "lead_summary": "",
        "matching_properties": [],
        "message": "",
        "channel": "email",
        "error": None,
    }

    final_state = await follow_up_graph.ainvoke(
        initial_state,
        config={"callbacks": []},
    )
    return {
        "message": final_state["message"],
        "channel": final_state["channel"],
    }

    # NOTE: nodes that need DB access need db injected.
    # For a cleaner pattern, pass db through the graph config:
    # config={"configurable": {"db": db}}
