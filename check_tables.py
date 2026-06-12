import asyncio
import sys
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

async def check():
    url = os.getenv("DATABASE_URL")

    engine = create_async_engine(url)

    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
                """
            )
        )

        tables = [r[0] for r in result]
        print("Tables in DB:", tables)

    await engine.dispose()

asyncio.run(check())


