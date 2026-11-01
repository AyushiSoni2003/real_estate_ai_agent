from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.api.v1 import properties as properties_api
from app.services import search, vector_store


def test_extract_location_hints_finds_multiple_locations():
    hints = search._extract_location_hints(
        "Find a cozy flat near good schools with parking in Bandra"
    )

    assert hints == ["good schools", "Bandra"]


@pytest.mark.asyncio
async def test_geocoded_location_with_no_nearby_listings_returns_empty(
    monkeypatch,
):
    monkeypatch.setattr(
        search, "_extract_location_hints", lambda query: ["Bandra"]
    )
    monkeypatch.setattr(
        search, "geocode_location", AsyncMock(return_value=(19.06, 72.83))
    )
    monkeypatch.setattr(
        search, "_postgis_radius_search", AsyncMock(return_value=set())
    )
    monkeypatch.setattr(
        search,
        "search_similar_properties",
        AsyncMock(return_value=[{"property_id": str(uuid4()), "score": 0.9}]),
    )
    fetch_properties = AsyncMock()
    monkeypatch.setattr(search, "_fetch_properties_by_ids", fetch_properties)

    db = object()
    agent_id = str(uuid4())
    results = await search.semantic_property_search(
        query="cozy flat in Bandra", db=db, agent_id=agent_id
    )

    assert results == []
    fetch_properties.assert_awaited_once_with([], db, agent_id)


@pytest.mark.asyncio
async def test_search_fetches_only_nearby_semantic_matches(monkeypatch):
    nearby_id = uuid4()
    outside_id = uuid4()
    agent_id = str(uuid4())
    nearby_property = SimpleNamespace(id=nearby_id)

    monkeypatch.setattr(
        search, "_extract_location_hints", lambda query: ["Bandra"]
    )
    monkeypatch.setattr(
        search, "geocode_location", AsyncMock(return_value=(19.06, 72.83))
    )
    monkeypatch.setattr(
        search,
        "_postgis_radius_search",
        AsyncMock(return_value={str(nearby_id)}),
    )
    monkeypatch.setattr(
        search,
        "search_similar_properties",
        AsyncMock(return_value=[
            {"property_id": str(outside_id), "score": 0.99},
            {"property_id": str(nearby_id), "score": 0.85},
        ]),
    )
    fetch_properties = AsyncMock(return_value=[nearby_property])
    monkeypatch.setattr(search, "_fetch_properties_by_ids", fetch_properties)

    db = object()
    results = await search.semantic_property_search(
        query="cozy flat in Bandra", db=db, agent_id=agent_id
    )

    assert results == [{"property": nearby_property, "similarity_score": 0.85}]
    fetch_properties.assert_awaited_once_with(
        [str(nearby_id)], db, agent_id
    )


@pytest.mark.asyncio
async def test_qdrant_search_always_filters_available_and_agent(monkeypatch):
    monkeypatch.setattr(
        vector_store, "embed_text", AsyncMock(return_value=[0.1, 0.2])
    )
    qdrant_query = Mock(return_value=SimpleNamespace(points=[]))
    monkeypatch.setattr(vector_store.qdrant, "query_points", qdrant_query)

    await vector_store.search_similar_properties("family home", agent_id="agent-1")

    conditions = qdrant_query.call_args.kwargs["query_filter"].must
    filters = {condition.key: condition.match.value for condition in conditions}
    assert filters == {"is_available": True, "agent_id": "agent-1"}


@pytest.mark.asyncio
async def test_database_fetch_filters_available_properties_by_agent(monkeypatch):
    agent_id = uuid4()
    property_id = uuid4()
    db = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: [])
            )
        )
    )

    await search._fetch_properties_by_ids([str(property_id)], db, str(agent_id))

    statement = db.execute.call_args.args[0]
    sql = str(statement)
    assert "properties.is_available IS true" in sql
    assert "properties.agent_id" in sql


@pytest.mark.asyncio
async def test_postgis_radius_query_is_scoped_to_agent():
    agent_id = uuid4()
    db = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(fetchall=Mock(return_value=[]))
        )
    )

    await search._postgis_radius_search(
        lat=19.06,
        lng=72.83,
        radius_km=10,
        db=db,
        agent_id=str(agent_id),
    )

    statement, params = db.execute.call_args.args
    assert "AND agent_id = :agent_id" in str(statement)
    assert params["agent_id"] == agent_id


@pytest.mark.asyncio
async def test_semantic_search_api_uses_authenticated_agents_id(monkeypatch):
    agent = SimpleNamespace(id=uuid4())
    db = object()
    service = AsyncMock(return_value=[])
    monkeypatch.setattr(properties_api, "semantic_property_search", service)

    await properties_api.semantic_search_properties(
        query="cozy apartment", radius_km=5, top_k=3,
        current_user=agent, db=db,
    )

    service.assert_awaited_once_with(
        query="cozy apartment",
        db=db,
        agent_id=str(agent.id),
        radius_km=5,
        top_k=3,
    )
