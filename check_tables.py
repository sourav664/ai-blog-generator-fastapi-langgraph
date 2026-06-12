import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys

if sys.platform == "win32": asyncio.set_event_loop_policy( asyncio.WindowsSelectorEventLoopPolicy() )
load_dotenv()

async def check():
    engine = create_async_engine(os.getenv("DATABASE_URL"))

    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT version_num FROM alembic_version")
        )

        print(result.fetchall())

    await engine.dispose()

asyncio.run(check())