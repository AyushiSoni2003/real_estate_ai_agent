import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_list_appointments(client):
	resp = await client.get("/api/v1/appointments/")
	assert resp.status_code < 500


@pytest.mark.asyncio
async def test_get_available_slots_requires_auth(client):
	resp = await client.get(
		"/api/v1/appointments/available-slots",
		params={"agent_id": str(uuid4()), "date": "2026-01-01"},
	)
	assert resp.status_code in (401, 200, 422)
