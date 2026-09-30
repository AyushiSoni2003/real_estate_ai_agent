import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import Base, get_db
import importlib
from app.models.agent_availability import AgentAvailability  # noqa: F401
from app.models.conversation_state import ConversationState  # noqa: F401
import uuid

# Importing this package registers the application's existing mapped tables.
importlib.import_module("app.models")


@pytest.fixture
async def client():
    # Each test gets a fresh in-memory database. This keeps API tests away
    # from the developer's PostgreSQL database and avoids sharing asyncpg
    # connections across pytest event loops.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        await engine.dispose()


@pytest.fixture
def any_uuid():
    return uuid.uuid4()
