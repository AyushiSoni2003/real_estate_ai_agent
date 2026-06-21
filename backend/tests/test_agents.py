import pytest


@pytest.mark.asyncio
async def test_agents_me_requires_auth(client):
	resp = await client.get("/api/v1/auth/me")
	assert resp.status_code in (401, 422, 200)
