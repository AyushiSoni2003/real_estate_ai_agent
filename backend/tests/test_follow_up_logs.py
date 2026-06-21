import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_get_lead_follow_ups(client):
    resp = await client.get(f"/api/v1/follow-ups/leads/{uuid4()}/follow-ups")
    assert resp.status_code < 500
