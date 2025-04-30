import grpc
from functools import wraps

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from .config import settings
from .models import Base

engine = create_async_engine(
    settings.db_uri
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False
)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

