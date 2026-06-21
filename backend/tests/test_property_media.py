import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_list_property_media(client):
    resp = await client.get(f"/api/v1/properties/{uuid4()}/media")
    assert resp.status_code < 500
