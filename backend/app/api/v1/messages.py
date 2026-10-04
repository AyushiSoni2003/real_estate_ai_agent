"""Messages API endpoints."""
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from twilio.request_validator import RequestValidator
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.message import Message
from app.models.message import MessageChannel, MessageDirection, MessageStatus
from app.models.agent import Agent
from app.models.lead import Lead
from app.models.conversation_state import ConversationState
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/webhooks/twilio/whatsapp", include_in_schema=False)
async def receive_whatsapp_message(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive a Twilio WhatsApp reply and continue its active negotiation."""
    form = await request.form()
    form_values = {key: str(value) for key, value in form.items()}
    signature = request.headers.get("X-Twilio-Signature", "")
    if not settings.TWILIO_AUTH_TOKEN or not signature:
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    if not validator.validate(str(request.url), form_values, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    sender = form_values.get("From", "").strip()
    body = form_values.get("Body", "").strip()
    external_id = form_values.get("MessageSid", "").strip()
    if not sender or not body or not external_id:
        raise HTTPException(
            status_code=400,
            detail="Twilio message is missing From, Body, or MessageSid",
        )

    # Twilio sends values like "whatsapp:+15551234567". Lead phone values
    # are normally stored as E.164 numbers, with or without that prefix.
    phone = sender.removeprefix("whatsapp:")
    result = await db.execute(
        select(Lead).where(func.replace(Lead.phone, "whatsapp:", "") == phone)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        return Response(content="<Response/>", media_type="application/xml")

    # Twilio can retry webhook deliveries, so do not process a known message
    # SID twice or create duplicate bookings/replies.
    duplicate = await db.execute(
        select(Message.id).where(Message.external_id == external_id)
    )
    if duplicate.scalar_one_or_none():
        return Response(content="<Response/>", media_type="application/xml")

    db.add(
        Message(
            lead_id=lead.id,
            channel=MessageChannel.WHATSAPP,
            direction=MessageDirection.INBOUND,
            status=MessageStatus.SENT,
            body=body,
            external_id=external_id,
        )
    )
    await db.flush()

    active_state = await db.execute(
        select(ConversationState.id).where(
            ConversationState.lead_id == lead.id,
            ConversationState.status == "negotiating",
        )
    )
    if active_state.scalar_one_or_none():
        from app.agents.appointment_graph import resume_appointment_flow
        from app.services.messaging import send_message as deliver_message

        state = await resume_appointment_flow(str(lead.id), body, db)
        reply = state.get("agent_message")
        if not reply and state.get("status") == "declined":
            reply = "Thanks for letting me know. If you would like to schedule a visit later, just message me."
        elif not reply and state.get("status") == "error":
            reply = "I couldn't find an available visit time right now. Please contact your agent and they can help schedule one."
        if reply:
            await deliver_message(lead, reply, "whatsapp", db)

    return Response(content="<Response/>", media_type="application/xml")


@router.post("/", response_model=MessageResponse, status_code=201)
async def send_message(
    data: MessageCreate,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to a lead."""
    message = Message(
        id=uuid4(),
        lead_id=data.lead_id,
        channel=data.channel,
        direction=data.direction or "outbound",
        body=data.body,
        external_id=data.external_id,
        status="sent"
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)
    return message


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get message details."""
    message = await db.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.get("/leads/{lead_id}/messages", response_model=list[MessageResponse])
async def get_lead_messages(
    lead_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get conversation history with a lead."""
    result = await db.execute(
        select(Message)
        .where(Message.lead_id == lead_id)
        .order_by(Message.sent_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.patch("/{message_id}", response_model=MessageResponse)
async def update_message_status(
    message_id: UUID,
    status: str = Query(..., description="Message status: sent, delivered, read, failed"),
    db: AsyncSession = Depends(get_db),
):
    """Update message status (mark as delivered/read)."""
    message = await db.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if status not in ["sent", "delivered", "read", "failed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    message.status = status
    
    if status == "delivered" and not message.delivered_at:
        message.delivered_at = func.now()
    elif status == "read" and not message.read_at:
        message.read_at = func.now()
    
    await db.flush()
    await db.refresh(message)
    return message


@router.delete("/{message_id}", status_code=204)
async def delete_message(
    message_id: UUID,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a message."""
    message = await db.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    await db.delete(message)
    await db.flush()


@router.get("/leads/{lead_id}/messages/unread-count")
async def get_unread_message_count(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get count of unread messages from a lead."""
    result = await db.execute(
        select(func.count(Message.id)).where(
            (Message.lead_id == lead_id) &
            (Message.status != "read") &
            (Message.direction == "inbound")
        )
    )
    count = result.scalar() or 0
    return {"lead_id": lead_id, "unread_count": count}
