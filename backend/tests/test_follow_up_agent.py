import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.models.lead import Lead, LeadStatus
from app.agents.conversation import run_follow_up_agent

def make_lead(**kwargs):
    defaults = dict(
        id=uuid4(),
        agent_id=uuid4(),
        full_name="Priya Sharma",
        email="priya@test.com",
        phone="+919876543210",
        status=LeadStatus.NEW,
        budget_min=3000000,
        budget_max=8000000,
        preferred_location="Bandra",
        notes="Looking for 2BHK near school",
    )
    return Lead(**{**defaults, **kwargs})

@pytest.mark.asyncio
async def test_agent_returns_message_and_channel():
    lead = make_lead()
    db = AsyncMock()

    db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(
        return_value=MagicMock(all=MagicMock(return_value=[]))
    )))

    with patch("app.agents.nodes.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(
            return_value=MagicMock(
                content="Hi Priya, hope you're well! We have some great 2BHK options in Bandra for you."
            )
        )
        result = await run_follow_up_agent(lead, 1, db)

    assert "message" in result
    assert "channel" in result
    assert result["channel"] == "whatsapp"
    assert "Priya" in result["message"]

@pytest.mark.asyncio
async def test_agent_uses_email_when_no_phone():
    lead = make_lead(phone=None)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    ))

    with patch("app.agents.nodes.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(
            return_value=MagicMock(content="Hi Priya, great properties available!")
        )
        result = await run_follow_up_agent(lead, 7, db)

    assert result["channel"] == "email"
