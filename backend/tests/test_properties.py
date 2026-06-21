import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_list_properties(client):
    resp = await client.get("/api/v1/properties/")
    assert resp.status_code < 500


@pytest.mark.asyncio
async def test_search_properties(client):
    resp = await client.get("/api/v1/properties/search", params={"city": "Nowhere"})
    assert resp.status_code < 500
