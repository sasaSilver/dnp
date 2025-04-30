# tests/conftest.py
import pytest
import pytest_asyncio
import asyncio
import os
import grpc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Импорт ваших модулей
os.environ["db_uri"] = "sqlite+aiosqlite:///:memory:"
from src.models.base import Base
from src.server import PhonebookService
from proto import phonebook_pb2_grpc

# Настройка event loop для pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Очищаем
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture
async def test_session(test_engine):
    async_session = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        yield session
        await session.commit()

@pytest_asyncio.fixture(scope="module")
async def grpc_server():
    # Создаем сервер
    server = grpc.aio.server()
    service = PhonebookService()
    phonebook_pb2_grpc.add_PhonebookServicer_to_server(service, server)
    server.add_insecure_port("[::]:50052")
    await server.start()
    
    yield server
    
    # Останавливаем сервер
    await server.stop(grace=None)

@pytest_asyncio.fixture
async def grpc_stub(grpc_server):
    # Создаем канал и клиент, используя текущий event loop
    channel = grpc.aio.insecure_channel("localhost:50052")
    stub = phonebook_pb2_grpc.PhonebookStub(channel)
    
    yield stub
    
    await channel.close()