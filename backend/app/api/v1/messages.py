"""Messages API endpoints."""
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.message import Message
from app.models.agent import Agent
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter(prefix="/messages", tags=["messages"])


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
