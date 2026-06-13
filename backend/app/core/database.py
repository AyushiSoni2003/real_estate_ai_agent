"""Database configuration."""
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
import warnings

# Create engine lazily and tolerate missing async DB drivers during import
try:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=10,
        max_overflow=20,
    )

    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
except ModuleNotFoundError as e:
    warnings.warn(f"Database driver not available at import time: {e}")
    engine = None
    AsyncSessionLocal = None

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

"""
Why expire_on_commit=False? With async SQLAlchemy, 
accessing an expired attribute after commit triggers another DB query — 
but you're already outside the session. 
This setting keeps attributes accessible after commit.
"""