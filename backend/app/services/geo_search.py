"""Geo search service (PostGIS queries)."""
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import asyncio

geocoder = Nominatim(user_agent="realtyiq")

async def geocode_location(location_text: str) -> tuple[float, float] | None:
    """
    Converts a location string like "Bandra, Mumbai" to (lat, lng).
    Uses Nominatim (OpenStreetMap) — free and no API key required.
    For production, consider Google Maps Geocoding API for accuracy.
    """
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: geocoder.geocode(
                f"{location_text}, India",
                timeout=5,
            )
        )
        if result:
            return result.latitude, result.longitude
        return None
    except GeocoderTimedOut:
        return None
