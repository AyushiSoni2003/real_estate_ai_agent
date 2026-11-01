from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.property import Property
from app.services.vector_store import search_similar_properties
from app.services.geo_search import geocode_location
import re

async def semantic_property_search(
    query: str,
    db: AsyncSession,
    agent_id: str | None = None,
    radius_km: float = 10.0,
    top_k: int = 5,
) -> list[dict]:
    """
    Main search function. Combines Qdrant semantic search
    with PostGIS geo filtering.

    1. Extract location from query
    2. Geocode to lat/lng
    3. Run Qdrant similarity search (top-20)
    4. Run PostGIS radius filter
    5. Intersect + re-rank by similarity score
    6. Fetch full property data for top results
    """

    location_candidates = _extract_location_hints(query)
    geo_ids: set[str] | None = None

    for location in location_candidates:
        coords = await geocode_location(location)
        if coords:
            lat, lng = coords
            geo_ids = await _postgis_radius_search(
                lat=lat,
                lng=lng,
                radius_km=radius_km,
                db=db,
                agent_id=agent_id,
            )
            break

    vector_results = await search_similar_properties(
        query_text=query,
        top_k=20,
        agent_id=agent_id,
    )

    if geo_ids is None:
        # If location extraction or geocoding produced no usable coordinates,
        # keep semantic search useful without a geographic constraint.
        filtered = vector_results
    else:
        # Keep the radius constraint strict. An empty intersection means there
        # are no semantic matches inside the requested area; never return
        # listings outside that area as a fallback.
        filtered = [
            result for result in vector_results
            if result["property_id"] in geo_ids
        ]

    top_ids = [r["property_id"] for r in filtered[:top_k]]
    score_map = {r["property_id"]: r["score"] for r in filtered}

    properties = await _fetch_properties_by_ids(top_ids, db, agent_id)

    return [
        {
            "property": prop,
            "similarity_score": round(score_map.get(str(prop.id), 0), 4),
        }
        for prop in properties
    ]

def _extract_location_hints(query: str) -> list[str]:
    """
    Simple rule-based location extractor.
    Looks for patterns like "near X", "in X", "at X".
    In Phase 5 you can upgrade this to a GPT-4o NER call.
    """
    pattern = re.compile(
        r"\b(?:near|in|at|around)\s+"
        r"([A-Za-z][A-Za-z\s'-]*?)"
        r"(?=\s+(?:near|in|at|around|with|and|for|under|below|above|within|that|which)\b|[,.;!?]|$)",
        re.IGNORECASE,
    )
    return [
        match.group(1).strip()
        for match in pattern.finditer(query)
        if len(match.group(1).strip()) > 2
    ]

async def _postgis_radius_search(
    lat: float,
    lng: float,
    radius_km: float,
    db: AsyncSession,
    agent_id: str | None = None,
) -> set[str]:
    """
    Returns IDs of all properties within radius_km of the given point.
    ST_DWithin with geography type measures in metres — divide km by 1000.
    """
    radius_metres = radius_km * 1000
    agent_filter = "AND agent_id = :agent_id" if agent_id else ""
    sql = text(f"""
        SELECT id::text
        FROM properties
        WHERE location IS NOT NULL
        AND ST_DWithin(
            location::geography,
            ST_MakePoint(:lng, :lat)::geography,
            :radius
        )
        AND is_available = true
        {agent_filter}
    """)
    params = {"lat": lat, "lng": lng, "radius": radius_metres}
    if agent_id:
        params["agent_id"] = UUID(agent_id)
    result = await db.execute(sql, params)
    return {row[0] for row in result.fetchall()}

async def _fetch_properties_by_ids(
    ids: list[str],
    db: AsyncSession,
    agent_id: str | None = None,
) -> list[Property]:
    if not ids:
        return []
    filters = [
        Property.id.in_([UUID(property_id) for property_id in ids]),
        Property.is_available.is_(True),
    ]
    if agent_id:
        filters.append(Property.agent_id == UUID(agent_id))
    result = await db.execute(
        select(Property).where(*filters)
    )
    props = result.scalars().all()
    id_order = {pid: idx for idx, pid in enumerate(ids)}
    return sorted(props, key=lambda p: id_order.get(str(p.id), 999))
