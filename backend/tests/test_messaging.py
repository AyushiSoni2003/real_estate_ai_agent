import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.models.lead import Lead, LeadStatus
from app.services.messaging import send_message

def make_lead(**kw):
    return Lead(
        id=uuid4(), agent_id=uuid4(),
        full_name="Raj Mehta",
        email="raj@test.com",
        phone="+919876543210",
        status=LeadStatus.NEW,
    )

@pytest.mark.asyncio
async def test_send_whatsapp_message():
    lead = make_lead()
    db = AsyncMock()

    with patch("app.services.messaging.twilio_client") as mock_twilio:
        mock_msg = MagicMock()
        mock_msg.sid = "SM123456"
        mock_twilio.messages.create.return_value = mock_msg

        msg = await send_message(lead, "Hello Raj!", "whatsapp", db)

    mock_twilio.messages.create.assert_called_once()
    call_kwargs = mock_twilio.messages.create.call_args[1]
    assert "whatsapp" in call_kwargs["to"]
    db.add.assert_called_once()

@pytest.mark.asyncio
async def test_send_email_message():
    lead = make_lead(phone=None)
    db = AsyncMock()

    with patch("app.services.messaging.sg_client") as mock_sg:
        mock_response = MagicMock()
        mock_response.headers = {"X-Message-Id": "email-abc"}
        mock_sg.send.return_value = mock_response

        msg = await send_message(lead, "Hello Raj!", "email", db)

    mock_sg.send.assert_called_once()
    db.add.assert_called_once()
