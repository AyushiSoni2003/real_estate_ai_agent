import asyncio
import asyncpg
from app.core.config import settings

async def main():
    url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://",
        "postgresql://"
    )

    conn = await asyncpg.connect(url)

    await conn.execute("DROP TABLE IF EXISTS alembic_version")

    print("Dropped stale alembic_version table.")

    await conn.close()

asyncio.run(main())
