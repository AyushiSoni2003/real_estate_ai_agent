"""Leads API endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse

router = APIRouter(prefix="/leads", tags=["leads"])

@router.post("/", response_model=LeadResponse, status_code=201)
async def create_lead(
    data: LeadCreate,
    db: AsyncSession = Depends(get_db),
):
    # TODO: Replace hardcoded agent_id with current user from JWT
    from uuid import uuid4
    lead = Lead(**data.model_dump(), agent_id=uuid4())
    db.add(lead)
    await db.flush()
    await db.refresh(lead)
    return lead

@router.get("/", response_model=list[LeadResponse])
async def list_leads(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    data: LeadUpdate,
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(lead, field, value)
    await db.flush()
    await db.refresh(lead)
    return lead

@router.delete("/{lead_id}", status_code=204)
async def delete_lead(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    await db.delete(lead)
    return None
