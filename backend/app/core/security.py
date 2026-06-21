"""Security utilities for authentication, token management, and password hashing."""
from datetime import datetime, timedelta
from typing import Optional
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from app.core.database import get_db
from app.schemas.auth import TokenData
from app.models.agent import Agent

# ============================================================================
# PASSWORD HASHING CONFIGURATION
# ============================================================================
# CryptContext: Manages password hashing with bcrypt algorithm
# bcrypt: Industry standard, resistant to GPU attacks, includes salt & rounds
# deprecated: Marks older hash schemes as deprecated (future upgrade path)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Security level: 12 rounds (higher = slower but more secure)
)

# ============================================================================
# JWT CONFIGURATION
# ============================================================================
# These should ideally come from environment variables for production
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
ALGORITHM = "HS256"  # HMAC with SHA-256: Fast, suitable for signature verification
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short expiration: 15 minutes for security
REFRESH_TOKEN_EXPIRE_DAYS = 7  # Longer expiration for refresh tokens

# HTTP Bearer scheme for automatic token extraction from Authorization header
security = HTTPBearer()


# ============================================================================
# PASSWORD HASHING FUNCTIONS
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    
    Why bcrypt?
    - Adaptive: Configurable rounds parameter makes it future-proof
    - Salt: Automatically generates unique salt for each password
    - Resistant: GPU/ASIC resistant due to memory requirements
    - Standard: Industry standard for password storage
    
    Args:
        password: Plain-text password from user
        
    Returns:
        Hashed password (can be safely stored in database)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against its bcrypt hash.
    
    Why this matters:
    - Never store plain passwords
    - Always verify at login time
    - Returns False for invalid passwords
    
    Args:
        plain_password: Password provided by user during login
        hashed_password: Hash stored in database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT TOKEN FUNCTIONS
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    JWT Structure:
    - Header: {"alg": "HS256", "typ": "JWT"}
    - Payload: {"sub": user_id, "email": user_email, "scopes": [...], "exp": expiry_time}
    - Signature: HMAC-SHA256(header.payload, SECRET_KEY)
    
    Why JWT?
    - Stateless: No server-side session storage needed
    - Scalable: Works across multiple servers/replicas
    - Self-contained: All user info in token
    - Standard: Widely supported across APIs
    
    Why separate access tokens?
    - Short expiration (15 min): Reduces impact if token is compromised
    - Refresh tokens: Allow users to get new tokens without re-login
    
    Args:
        data: Dictionary with token claims (must include "sub" for user ID)
        expires_delta: Custom expiration time (defaults to ACCESS_TOKEN_EXPIRE_MINUTES)
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add expiration time to payload
    to_encode.update({"exp": expire})
    
    # Encode and sign token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.
    
    Verification checks:
    - Signature: Token wasn't tampered with
    - Expiration: Token hasn't expired
    - Algorithm: Uses correct signing algorithm
    
    Args:
        token: JWT token string from Authorization header
        
    Returns:
        Decoded token payload (dictionary with claims)
        
    Raises:
        HTTPException: If token is invalid, expired, or malformed
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(email=email, scopes=payload.get("scopes", []))
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


# ============================================================================
# FASTAPI DEPENDENCY FUNCTIONS
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Agent:
    """
    FastAPI dependency to extract and validate JWT token from request.
    
    How it works:
    1. HTTPBearer automatically extracts token from "Authorization: Bearer <token>"
    2. verify_token() decodes and validates JWT
    3. Database query fetches the Agent object
    4. Returns Agent object for use in route handlers
    
    Why use a dependency?
    - Reusable: Use as Depends(get_current_user) on any protected route
    - Automatic: FastAPI extracts token from header for us
    - Secure: Validates token before handler code runs
    - Clean: Keeps security logic separate from route logic
    
    Raises:
        HTTPException: 401 Unauthorized if token invalid/expired or user not found
        
    Returns:
        Agent: The authenticated user object from database
    """
    token = credentials.credentials
    token_data = verify_token(token)
    
    # Query database for agent
    result = await db.execute(
        select(Agent).where(Agent.email == token_data.email)
    )
    agent = result.scalars().first()
    
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return agent


async def get_current_active_user(
    current_user: Agent = Depends(get_current_user),
) -> Agent:
    """
    Additional dependency to ensure user account is active.
    
    Why separate from get_current_user?
    - Allows selective enforcement: Some routes may allow inactive users
    - Cleaner: Single responsibility principle
    - Flexible: Can add other checks (e.g., premium membership)
    
    Raises:
        HTTPException: 403 Forbidden if user account is inactive
        
    Returns:
        Agent: The active authenticated user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user
