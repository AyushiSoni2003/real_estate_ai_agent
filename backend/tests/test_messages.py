import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_get_messages_history(client):
    resp = await client.get(f"/api/v1/messages/leads/{uuid4()}/messages")
    assert resp.status_code < 500
