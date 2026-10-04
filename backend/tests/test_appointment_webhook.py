from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_current_user
from app.main import app as fastapi_app
from app.models.agent import Agent
from app.models.conversation_state import ConversationState
from app.models.lead import Lead
from app.models.message import Message, MessageDirection


@pytest.mark.asyncio
async def test_twilio_reply_resumes_active_negotiation_and_sends_agent_reply(
    client, db_session, appointment_flow, monkeypatch
):
    graph_module, _ = appointment_flow
    agent_id = uuid4()
    lead_id = uuid4()
    lead = Lead(
        id=lead_id,
        agent_id=agent_id,
        full_name="Test Lead",
        phone="+15551234567",
    )
    db_session.add_all([
        Agent(
            id=agent_id,
            email=f"agent-{agent_id}@example.com",
            hashed_password="not-a-real-password-hash",
            full_name="Test Agent",
        ),
        lead,
        ConversationState(
            lead_id=lead_id,
            graph_state="{}",
            status="negotiating",
        ),
    ])
    await db_session.flush()

    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "test-token")
    from app.api.v1 import messages as messages_api

    monkeypatch.setattr(
        messages_api.RequestValidator,
        "validate",
        lambda self, url, params, signature: True,
    )
    resume = AsyncMock(return_value={
        "status": "negotiating",
        "agent_message": "Would Thursday at 10 work for you?",
    })
    monkeypatch.setattr(graph_module, "resume_appointment_flow", resume)

    import app.services.messaging as messaging_service

    deliver = AsyncMock()
    monkeypatch.setattr(messaging_service, "send_message", deliver)
    payload = {
        "From": "whatsapp:+15551234567",
        "Body": "Can you send me another time?",
        "MessageSid": "SM-test-inbound-1",
    }

    first_response = await client.post(
        "/api/v1/messages/webhooks/twilio/whatsapp",
        data=payload,
        headers={"X-Twilio-Signature": "test-signature"},
    )
    second_response = await client.post(
        "/api/v1/messages/webhooks/twilio/whatsapp",
        data=payload,
        headers={"X-Twilio-Signature": "test-signature"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.headers["content-type"].startswith("application/xml")
    resume.assert_awaited_once_with(str(lead_id), payload["Body"], db_session)
    deliver.assert_awaited_once_with(
        lead, "Would Thursday at 10 work for you?", "whatsapp", db_session
    )
    inbound_messages = (await db_session.execute(
        select(Message).where(Message.external_id == payload["MessageSid"])
    )).scalars().all()
    assert len(inbound_messages) == 1
    assert inbound_messages[0].direction == MessageDirection.INBOUND


@pytest.mark.asyncio
async def test_agent_can_start_negotiation_for_owned_lead(
    client, db_session, appointment_flow, monkeypatch
):
    graph_module, _ = appointment_flow
    agent_id = uuid4()
    lead_id = uuid4()
    agent = Agent(
        id=agent_id,
        email=f"owner-{agent_id}@example.com",
        hashed_password="not-a-real-password-hash",
        full_name="Test Agent",
    )
    lead = Lead(
        id=lead_id,
        agent_id=agent_id,
        full_name="Test Lead",
        phone="+15551234567",
    )
    db_session.add_all([agent, lead])
    await db_session.flush()

    start = AsyncMock(return_value={
        "status": "negotiating",
        "agent_message": "Which visit time works for you?",
    })
    monkeypatch.setattr(graph_module, "start_appointment_flow", start)
    import app.api.v1.appointments as appointments_api

    deliver = AsyncMock()
    monkeypatch.setattr(appointments_api, "send_message", deliver)
    fastapi_app.dependency_overrides[get_current_user] = lambda: agent
    try:
        response = await client.post(
            f"/api/v1/appointments/leads/{lead_id}/negotiation"
        )
    finally:
        fastapi_app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["status"] == "negotiating"
    start.assert_awaited_once()
    deliver.assert_awaited_once_with(
        lead, "Which visit time works for you?", "whatsapp", db_session
    )


@pytest.mark.asyncio
async def test_twilio_reply_rejects_invalid_signature(client, monkeypatch):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "test-token")
    from app.api.v1 import messages as messages_api

    monkeypatch.setattr(
        messages_api.RequestValidator,
        "validate",
        lambda self, url, params, signature: False,
    )
    response = await client.post(
        "/api/v1/messages/webhooks/twilio/whatsapp",
        data={
            "From": "whatsapp:+15551234567",
            "Body": "Thursday works",
            "MessageSid": "SM-forged",
        },
        headers={"X-Twilio-Signature": "invalid"},
    )
    assert response.status_code == 403
