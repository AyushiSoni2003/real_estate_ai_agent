import pytest


@pytest.mark.asyncio
async def test_create_lead_requires_auth(client):
	payload = {"full_name": "Test User", "email": "test@example.com", "phone": "555-0100"}
	resp = await client.post("/api/v1/leads/", json=payload)
	# Endpoint requires authentication; expect 401 Unauthorized
	assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_leads_endpoint(client):
	resp = await client.get("/api/v1/leads/")
	# Ensure endpoint does not return 5xx (DB may be unavailable in CI)
	assert resp.status_code < 500
