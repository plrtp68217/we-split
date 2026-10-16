import os
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session