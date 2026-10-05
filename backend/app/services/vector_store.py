"""Qdrant storage and OpenAI embeddings for property search."""

from openai import AsyncOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings


qdrant = QdrantClient(url=settings.QDRANT_URL)
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def init_qdrant_collection() -> None:
    """Create the properties collection if it does not already exist."""
    existing = [collection.name for collection in qdrant.get_collections().collections]
    if settings.QDRANT_COLLECTION_NAME not in existing:
        qdrant.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=settings.OPENAI_EMBEDDING_DIMENSIONS,
                distance=Distance.COSINE,
            ),
        )
        print(f"Created Qdrant collection: {settings.QDRANT_COLLECTION_NAME}")


async def embed_text(text: str) -> list[float]:
    """Generate an embedding for a property description or search query."""
    response = await openai_client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=text,
        # OpenAI Python 1.3.6 does not expose `dimensions` as a named argument.
        extra_body={"dimensions": settings.OPENAI_EMBEDDING_DIMENSIONS},
    )
    return response.data[0].embedding


async def index_property(property_id: str, text: str, payload: dict) -> None:
    """Embed a property description and store it in Qdrant with its metadata."""
    vector = await embed_text(text)
    qdrant.upsert(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points=[
            PointStruct(
                id=property_id,
                vector=vector,
                payload={
                    "agent_id": payload.get("agent_id"),
                    "city": payload.get("city"),
                    "price": payload.get("price"),
                    "bedrooms": payload.get("bedrooms"),
                    "is_available": payload.get("is_available", True),
                    **payload,
                },
            )
        ],
    )


async def search_similar_properties(
    query_text: str,
    top_k: int = 20,
    agent_id: str | None = None,
) -> list[dict]:
    """Return similar property IDs, scores, and payloads from Qdrant."""
    query_vector = await embed_text(query_text)

    query_filter = None
    if agent_id:
        query_filter = Filter(
            must=[
                FieldCondition(key="agent_id", match=MatchValue(value=agent_id)),
                FieldCondition(
                    key="is_available",
                    match=MatchValue(value=True),
                ),
            ]
        )

    results = qdrant.query_points(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    )

    return [
        {"property_id": str(point.id), "score": point.score, "payload": point.payload}
        for point in results.points
    ]


async def delete_property_vector(property_id: str) -> None:
    """Delete a property's vector from Qdrant."""
    qdrant.delete(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points_selector=[property_id],
    )
