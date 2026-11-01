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
            )
            break

    vector_results = await search_similar_properties(
        query_text=query,
        top_k=20,
        agent_id=agent_id,
    )

    if geo_ids is not None:
        filtered = [
            r for r in vector_results
            if r["property_id"] in geo_ids
        ]
    else:
        filtered = vector_results

    if not filtered:
        filtered = vector_results[:top_k]

    top_ids = [r["property_id"] for r in filtered[:top_k]]
    score_map = {r["property_id"]: r["score"] for r in filtered}

    properties = await _fetch_properties_by_ids(top_ids, db)

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
) -> set[str]:
    """
    Returns IDs of all properties within radius_km of the given point.
    ST_DWithin with geography type measures in metres — divide km by 1000.
    """
    radius_metres = radius_km * 1000
    sql = text("""
        SELECT id::text
        FROM properties
        WHERE location IS NOT NULL
        AND ST_DWithin(
            location::geography,
            ST_MakePoint(:lng, :lat)::geography,
            :radius
        )
        AND is_available = true
    """)
    result = await db.execute(sql, {
        "lat": lat, "lng": lng, "radius": radius_metres
    })
    return {row[0] for row in result.fetchall()}

async def _fetch_properties_by_ids(
    ids: list[str],
    db: AsyncSession,
) -> list[Property]:
    if not ids:
        return []
    result = await db.execute(
        select(Property).where(
            Property.id.in_([UUID(i) for i in ids])
        )
    )
    props = result.scalars().all()
    id_order = {pid: idx for idx, pid in enumerate(ids)}
    return sorted(props, key=lambda p: id_order.get(str(p.id), 999))
