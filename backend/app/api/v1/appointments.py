"""Appointments API endpoints."""
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.appointment import Appointment
from app.models.agent import Agent
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_appointment(
    data: AppointmentCreate,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Schedule a new appointment."""
    appointment = Appointment(
        id=uuid4(),
        agent_id=current_user.id,
        lead_id=data.lead_id,
        property_id=data.property_id,
        scheduled_at=data.scheduled_at,
        notes=data.notes,
        status="scheduled"
    )
    db.add(appointment)
    await db.flush()
    await db.refresh(appointment)
    return appointment


@router.get("/", response_model=list[AppointmentResponse])
async def list_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    agent_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all appointments with pagination."""
    query = select(Appointment)
    if agent_id:
        query = query.where(Appointment.agent_id == agent_id)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get appointment details."""
    appointment = await db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: UUID,
    data: AppointmentUpdate,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update appointment (reschedule or change status)."""
    appointment = await db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if appointment.agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this appointment")
    
    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(appointment, key, value)
    
    await db.flush()
    await db.refresh(appointment)
    return appointment


@router.delete("/{appointment_id}", status_code=204)
async def delete_appointment(
    appointment_id: UUID,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an appointment."""
    appointment = await db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if appointment.agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this appointment")
    
    await db.delete(appointment)
    await db.flush()


@router.get("/leads/{lead_id}/appointments", response_model=list[AppointmentResponse])
async def get_lead_appointments(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all appointments for a specific lead."""
    result = await db.execute(
        select(Appointment).where(Appointment.lead_id == lead_id)
    )
    return result.scalars().all()


@router.get("/available-slots")
async def get_available_slots(
    agent_id: UUID,
    date: str,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get available time slots for agent on a given date."""
    # TODO: Implement calendar integration to check agent availability
    return {
        "agent_id": agent_id,
        "date": date,
        "available_slots": [
            "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
            "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"
        ]
    }
