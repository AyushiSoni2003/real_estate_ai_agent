"""Authentication API endpoints."""
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, hash_password, get_current_user
from app.models.agent import Agent
from app.schemas.auth import UserLogin, Token, TokenData
from app.schemas.agent import AgentCreate, AgentResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AgentResponse, status_code=201)
async def register(data: AgentCreate, db: AsyncSession = Depends(get_db)):
    """Register a new agent."""
    # Check if email already exists
    result = await db.execute(select(Agent).where(Agent.email == data.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create new agent
    agent = Agent(
        id=uuid4(),
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(data.password),
        phone=data.phone,
        is_active=True,
        role=data.role or "agent"
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    # Support both email and username
    identifier = credentials.username
    
    result = await db.execute(
        select(Agent).where(
            (Agent.email == identifier) | (Agent.full_name == identifier)
        )
    )
    agent = result.scalars().first()
    
    if not agent or not verify_password(credentials.password, agent.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": str(agent.id), "email": agent.email, "scopes": ["agent"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: TokenData = Depends(get_current_user)):
    """Refresh JWT token."""
    access_token = create_access_token(
        data={"sub": current_user.email, "scopes": current_user.scopes or ["agent"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=AgentResponse)
async def get_current_agent(current_user: Agent = Depends(get_current_user)):
    """Get current authenticated agent."""
    return current_user


@router.post("/logout")
async def logout(current_user: Agent = Depends(get_current_user)):
    """Logout (invalidate token on client side)."""
    return {"message": "Successfully logged out. Please clear the token from client."}
