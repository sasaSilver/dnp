# tests/test_phonebook.py
import pytest
from sqlalchemy import select

from src.models.contact import ContactSchema

# Маркер для асинхронных тестов
pytestmark = pytest.mark.asyncio

async def test_db_connection(test_session):
    """Проверяем, что соединение с БД работает"""
    # Просто проверяем, что сессия создаётся без ошибок
    assert test_session is not None

async def test_create_contact(test_session):
    """Тестируем создание контакта напрямую через БД"""
    # Создаём тестовый контакт
    contact = ContactSchema(name="Test Contact", phone_number="+1234567890")
    test_session.add(contact)
    await test_session.commit()
    await test_session.refresh(contact)
    
    # Проверяем, что запись создана
    assert contact.id is not None
    
    # Проверяем, что можем найти запись по имени
    result = await test_session.execute(
        select(ContactSchema).where(ContactSchema.name == "Test Contact")
    )
    found_contact = result.scalar_one_or_none()
    assert found_contact is not None
    assert found_contact.phone_number == "+1234567890"