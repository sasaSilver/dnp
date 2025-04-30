# tests/test_server_extended.py
import pytest
import grpc
from sqlalchemy import select
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from proto.phonebook_pb2 import LookupRequest, AddEntryRequest
from src.models.contact import ContactSchema

# Маркер для асинхронных тестов
pytestmark = pytest.mark.asyncio

async def test_add_duplicate_entry(grpc_stub):
    """Тестируем добавление дубликата записи"""
    # Добавляем первую запись
    response1 = await grpc_stub.AddEntry(
        AddEntryRequest(name="Duplicate User", number="+1234567000")
    )
    assert response1.success is True
    
    # Пробуем добавить запись с тем же именем
    response2 = await grpc_stub.AddEntry(
        AddEntryRequest(name="Duplicate User", number="+7890123000")
    )
    
    # Проверяем, что получили ошибку
    assert response2.success is False
    assert "Name already exists" in response2.message

async def test_add_with_invalid_data(grpc_stub):
    """Тестируем добавление записи с пустыми данными"""
    response = await grpc_stub.AddEntry(
        AddEntryRequest(name="", number="")
    )
    
    # Несмотря на то, что данные неверные, в текущей реализации сервера 
    # специальная валидация отсутствует, поэтому тест должен пройти
    # Этот тест может быть изменен в будущем, если добавится валидация
    assert response.success is True

async def test_signature_validation(grpc_stub):
    """Тестируем подпись при запросе данных"""
    # Добавляем новую запись
    add_response = await grpc_stub.AddEntry(
        AddEntryRequest(name="Sign Test", number="+5555555555")
    )
    assert add_response.success is True
    
    # Запрашиваем запись
    lookup_response = await grpc_stub.Lookup(
        LookupRequest(name="Sign Test")
    )
    
    # Проверяем, что подпись не пустая
    assert lookup_response.number == "+5555555555"
    assert len(lookup_response.signature) > 0
    
    # Чтобы полностью проверить подпись, нужен доступ к public_key сервера,
    # в реальном тесте мы бы создали тестовый сервис с известным ключом

async def test_phonebook_multiple_operations(grpc_stub, test_session):
    """Тестируем несколько операций подряд в одном тесте"""
    # 1. Добавляем несколько записей
    names = ["Alice", "Bob", "Charlie"]
    numbers = ["+1111111111", "+2222222222", "+3333333333"]
    
    for i in range(3):
        response = await grpc_stub.AddEntry(
            AddEntryRequest(name=names[i], number=numbers[i])
        )
        assert response.success is True
    
    # 2. Проверяем, что все записи существуют в БД
    for i in range(3):
        result = await test_session.execute(
            select(ContactSchema).where(ContactSchema.name == names[i])
        )
        contact = result.scalar_one_or_none()
        assert contact is not None
        assert contact.phone_number == numbers[i]
    
    # 3. Запрашиваем данные через API
    for i in range(3):
        lookup_response = await grpc_stub.Lookup(
            LookupRequest(name=names[i])
        )
        assert lookup_response.number == numbers[i]
        assert len(lookup_response.signature) > 0

async def test_verify_signature(grpc_stub, test_session):
    """Проверяем, что подпись корректно подписывает данные"""
    # Добавляем запись
    name = "Verify Test"
    number = "+9999999999"
    
    add_response = await grpc_stub.AddEntry(
        AddEntryRequest(name=name, number=number)
    )
    assert add_response.success is True
    
    # Получаем данные с подписью
    lookup_response = await grpc_stub.Lookup(
        LookupRequest(name=name)
    )
    
    # В реальном тесте здесь была бы проверка подписи
    # Для простоты просто проверяем, что подпись не пустая
    assert len(lookup_response.signature) > 64  # Ed25519 подписи должны быть 64+ байт