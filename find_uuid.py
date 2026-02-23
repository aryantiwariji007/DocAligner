
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

async def find_uuid():
    target_uuid = "b32a81d0-0653-45ef-a1f6-fabe1d0ea495"
    ports = [5433, 5432]
    
    for port in ports:
        url = f"postgresql+asyncpg://postgres:postgres@127.0.0.1:{port}/docstandards"
        try:
            engine = create_async_engine(url)
            async with engine.connect() as conn:
                # Get all tables
                result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
                tables = [row[0] for row in result]
                
                for table in tables:
                    try:
                        res = await conn.execute(text(f"SELECT * FROM {table}"))
                        columns = res.keys()
                        rows = res.fetchall()
                        for row in rows:
                            for i, val in enumerate(row):
                                if str(val) == target_uuid:
                                    print(f"MATCH FOUND!")
                                    print(f"Table: {table}")
                                    print(f"Column: {columns[i]}")
                                    print("Row Details:")
                                    for col, v in zip(columns, row):
                                        print(f"  {col}: {v}")
                                    return
                    except Exception as e:
                        pass
        except Exception as e:
            pass

    print("Search complete.")

if __name__ == "__main__":
    asyncio.run(find_uuid())
