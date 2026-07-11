from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.agents.state import AgentState
from app.models.property import Property
from app.models.lead import Lead
from app.core.config import settings

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    api_key=settings.GOOGLE_API_KEY,
    temperature=1.0,  # Gemini 3.0+ defaults to 1.0
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)


async def qualify_lead_node(state: AgentState, db: AsyncSession) -> AgentState:
    """
    Summarises the lead profile into a compact string
    that subsequent nodes use for context.
    """
    lead: Lead = state["lead"]
    summary = (
        f"Lead: {lead.full_name}. "
        f"Budget: {lead.budget_min}–{lead.budget_max} INR. "
        f"Preferred location: {lead.preferred_location or 'not specified'}. "
        f"Status: {lead.status}. "
        f"Notes: {lead.notes or 'none'}."
    )
    return {**state, "lead_summary": summary}

async def match_properties_node(state: AgentState, db: AsyncSession) -> AgentState:
    """
    Fetches up to 3 available properties that match the
    lead's location preference. In Phase 4 this becomes
    a vector search — for now it's a SQL query.
    """
    lead: Lead = state["lead"]
    query = (
        select(Property)
        .where(Property.is_available == True)
        .where(Property.agent_id == lead.agent_id)
    )
    if lead.preferred_location:
        query = query.where(
            Property.city.ilike(f"%{lead.preferred_location}%")
        )
    if lead.budget_max:
        query = query.where(Property.price <= lead.budget_max)

    result = await db.execute(query.limit(3))
    props = result.scalars().all()

    matching = [
        {
            "title": p.title,
            "address": p.address,
            "price": p.price,
            "bedrooms": p.bedrooms,
            "area_sqft": p.area_sqft,
        }
        for p in props
    ]
    return {**state, "matching_properties": matching}

async def generate_message_node(state: AgentState) -> AgentState:
    """
    Uses GPT-4o to write a personalised follow-up message.
    The system prompt defines tone and structure.
    The user prompt injects lead context and matched properties.
    """
    day = state["follow_up_day"]
    lead_summary = state["lead_summary"]
    properties = state["matching_properties"]

    day_context = {
        1:  "This is their first contact. Be warm and welcoming.",
        3:  "Check in gently. They may have questions.",
        7:  "Ask if they'd like to schedule a visit.",
        30: "Re-engage. Offer fresh options if available.",
    }

    prop_text = ""
    if properties:
        prop_text = "\n\nMatching properties for them:\n"
        for p in properties:
            prop_text += (
                f"- {p['title']} at {p['address']}, "
                f"₹{p['price']:,}, {p['bedrooms']} BHK, "
                f"{p['area_sqft']} sq ft\n"
            )

    system = (
        "You are a professional, friendly real estate assistant. "
        "Write short, conversational follow-up messages (under 120 words). "
        "Never sound like a template. Always use the lead's first name."
    )
    user = (
        f"Day {day} follow-up. {day_context.get(day, '')}\n"
        f"Lead profile: {lead_summary}"
        f"{prop_text}\n\n"
        "Write the follow-up message now."
    )

    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=user),
    ])
    return {**state, "message": response.content}

async def route_channel_node(state: AgentState) -> AgentState:
    """
    Decides which channel to use. Prefer WhatsApp if
    phone is available, fall back to email.
    """
    lead: Lead = state["lead"]
    channel = "whatsapp" if lead.phone else "email"
    return {**state, "channel": channel}
