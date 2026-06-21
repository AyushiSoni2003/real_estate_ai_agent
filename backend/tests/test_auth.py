import pytest


@pytest.mark.asyncio
async def test_login_bad_credentials(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "bad"},
    )
    # Should not be a server error; likely 401 or 422 when no user exists
    assert resp.status_code < 500
