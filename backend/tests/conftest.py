import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import uuid


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def any_uuid():
    return uuid.uuid4()
