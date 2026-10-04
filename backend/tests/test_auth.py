import pytest
from uuid import uuid4
from app.core.security import hash_password
from app.models.agent import Agent


@pytest.mark.asyncio
async def test_login_bad_credentials(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "bad"},
    )
    # Should not be a server error; likely 401 or 422 when no user exists
    assert resp.status_code < 500


@pytest.mark.asyncio
async def test_login_token_authenticates_agent(client, db_session):
    agent = Agent(
        id=uuid4(),
        email="login-test@example.com",
        hashed_password=hash_password("correct-horse-battery"),
        full_name="Login Test Agent",
    )
    db_session.add(agent)
    await db_session.flush()

    login = await client.post(
        "/api/v1/auth/login",
        json={"username": agent.email, "password": "correct-horse-battery"},
    )
    assert login.status_code == 200

    profile = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert profile.status_code == 200
    assert profile.json()["email"] == agent.email
