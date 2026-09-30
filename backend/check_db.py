import asyncio
import asyncpg
from app.core.config import settings

async def main():
    url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://",
        "postgresql://"
    )

    conn = await asyncpg.connect(url)

    rows = await conn.fetch("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)

    print("\nTables in realtyiq_db:")
    for row in rows:
        print(" -", row["tablename"])

    await conn.close()

asyncio.run(main())
