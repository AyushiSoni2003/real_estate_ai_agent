import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_get_lead_activities(client):
    resp = await client.get(f"/api/v1/leads/{uuid4()}/activities")
    assert resp.status_code < 500
