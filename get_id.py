import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/docstandards"

async def get_doc():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(text("SELECT id, filename FROM document LIMIT 1"))
        doc = result.fetchone()
        if doc:
            print(f"ID:{doc[0]}")
            print(f"FILENAME:{doc[1]}")
        else:
            print("NO_DOCS")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(get_doc())
