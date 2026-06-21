import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_get_ai_interactions(client):
    resp = await client.get(f"/api/v1/leads/{uuid4()}/ai-interactions")
    assert resp.status_code < 500
