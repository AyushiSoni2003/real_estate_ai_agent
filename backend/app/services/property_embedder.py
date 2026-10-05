"""Build and synchronize semantic property embeddings."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property
from app.services.vector_store import index_property


logger = logging.getLogger(__name__)


def build_embedding_text(prop: Property) -> str:
    """Describe the property in natural language for semantic retrieval."""
    parts: list[str] = []

    if prop.title:
        parts.append(prop.title)

    details: list[str] = []
    if prop.bedrooms == 0:
        details.append("studio")
    elif prop.bedrooms is not None:
        bedroom_label = "bedroom" if prop.bedrooms == 1 else "bedrooms"
        details.append(f"{prop.bedrooms} {bedroom_label}")
    if prop.bathrooms is not None:
        bathroom_label = "bathroom" if prop.bathrooms == 1 else "bathrooms"
        details.append(f"{prop.bathrooms} {bathroom_label}")
    if details:
        parts.append(f"{', '.join(details)} property")

    if prop.area_sqft is not None:
        parts.append(f"{prop.area_sqft} square feet")
    if prop.address:
        parts.append(f"Located at {prop.address}")
    if prop.city:
        parts.append(f"in {prop.city}")
    if prop.price is not None:
        parts.append(f"Priced at {prop.price:,} rupees")
    if prop.amenities:
        parts.append(f"Amenities include: {', '.join(prop.amenities)}")
    if prop.description:
        parts.append(prop.description)

    return ". ".join(parts)


async def embed_and_index_property(prop: Property) -> None:
    """Embed a property's searchable text and upsert it into Qdrant."""
    await index_property(
        property_id=str(prop.id),
        text=build_embedding_text(prop),
        payload={
            "agent_id": str(prop.agent_id),
            "city": prop.city,
            "price": prop.price,
            "bedrooms": prop.bedrooms,
            "bathrooms": prop.bathrooms,
            "area_sqft": prop.area_sqft,
            "is_available": prop.is_available,
            "latitude": prop.latitude,
            "longitude": prop.longitude,
        },
    )


async def bulk_embed_all_properties(db: AsyncSession) -> None:
    """Index existing properties that are not marked as indexed."""
    result = await db.execute(
        select(Property).where(Property.qdrant_indexed.is_(False))
    )
    properties = result.scalars().all()
    indexed_count = 0

    for prop in properties:
        try:
            await embed_and_index_property(prop)
            prop.qdrant_indexed = True
            indexed_count += 1
        except Exception:
            logger.exception("Failed to index property %s", prop.id)

    await db.commit()
    logger.info("Indexed %s of %s properties", indexed_count, len(properties))
