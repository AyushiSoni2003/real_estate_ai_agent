import pytest
from uuid import uuid4
from unittest.mock import AsyncMock
from types import SimpleNamespace

from fastapi import HTTPException
from app.api.v1 import properties as properties_api


@pytest.mark.asyncio
async def test_list_properties(client):
    resp = await client.get("/api/v1/properties/")
    assert resp.status_code < 500


@pytest.mark.asyncio
async def test_search_properties(client):
    resp = await client.get("/api/v1/properties/search", params={"city": "Nowhere"})
    assert resp.status_code < 500


@pytest.mark.asyncio
async def test_delete_property_removes_vector_and_database_row(
    monkeypatch,
):
    agent_id = uuid4()
    property_id = uuid4()
    agent = SimpleNamespace(id=agent_id)
    prop = SimpleNamespace(id=property_id, agent_id=agent_id)
    db = SimpleNamespace(
        get=AsyncMock(return_value=prop),
        delete=AsyncMock(),
        flush=AsyncMock(),
    )

    delete_vector = AsyncMock()
    monkeypatch.setattr(properties_api, "delete_property_vector", delete_vector)

    await properties_api.delete_property(property_id, agent, db)

    delete_vector.assert_awaited_once_with(str(property_id))
    db.delete.assert_awaited_once_with(prop)
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_property_does_not_remove_vector_for_other_agent(
    monkeypatch,
):
    owner_id = uuid4()
    other_agent = SimpleNamespace(id=uuid4())
    property_id = uuid4()
    prop = SimpleNamespace(id=property_id, agent_id=owner_id)
    db = SimpleNamespace(get=AsyncMock(return_value=prop))

    delete_vector = AsyncMock()
    monkeypatch.setattr(properties_api, "delete_property_vector", delete_vector)

    with pytest.raises(HTTPException) as exc_info:
        await properties_api.delete_property(property_id, other_agent, db)

    assert exc_info.value.status_code == 403
    delete_vector.assert_not_awaited()
