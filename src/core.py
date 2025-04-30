from functools import wraps
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from .config import settings
from .models import Base

engine = create_async_engine(
    settings.db_uri if not settings.testing else "sqlite+aiosqlite:///:memory:"
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False
)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def inject_session(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with get_db() as db:
            kwargs["db"] = db
            return await func(*args, **kwargs)
    return wrapper

