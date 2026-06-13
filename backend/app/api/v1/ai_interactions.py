"""AI Interactions API endpoints."""
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ai_interaction import AIInteraction
from app.models.agent import Agent
from app.schemas.ai_interaction import AIInteractionCreate, AIInteractionResponse

router = APIRouter(prefix="/leads", tags=["ai-interactions"])


@router.post("/{lead_id}/ai-interactions", response_model=AIInteractionResponse, status_code=201)
async def log_ai_interaction(
    lead_id: UUID,
    data: AIInteractionCreate,
    current_user: Agent = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log an AI interaction for a lead."""
    interaction = AIInteraction(
        id=uuid4(),
        lead_id=lead_id,
        interaction_type=data.interaction_type,
        prompt=data.prompt,
        response=data.response,
        model=data.model,
        tokens_used=data.tokens_used
    )
    db.add(interaction)
    await db.flush()
    await db.refresh(interaction)
    return interaction


@router.get("/{lead_id}/ai-interactions", response_model=list[AIInteractionResponse])
async def get_lead_ai_interactions(
    lead_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get all AI interactions for a lead."""
    result = await db.execute(
        select(AIInteraction)
        .where(AIInteraction.lead_id == lead_id)
        .order_by(AIInteraction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/ai-interactions/{interaction_id}", response_model=AIInteractionResponse)
async def get_ai_interaction(
    interaction_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get specific AI interaction details."""
    interaction = await db.get(AIInteraction, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="AI interaction not found")
    return interaction


@router.get("/{lead_id}/ai-recommendations")
async def get_property_recommendations(
    lead_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-generated property recommendations for a lead."""
    result = await db.execute(
        select(AIInteraction)
        .where(
            (AIInteraction.lead_id == lead_id) &
            (AIInteraction.interaction_type == "property_recommendation")
        )
        .order_by(AIInteraction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    interactions = result.scalars().all()
    return {
        "lead_id": lead_id,
        "recommendations": [
            {"id": i.id, "response": i.response, "created_at": i.created_at}
            for i in interactions
        ]
    }
