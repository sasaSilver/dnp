# tests/test_db.py
import pytest
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from src.models.contact import ContactSchema

# Маркер для асинхронных тестов
pytestmark = pytest.mark.asyncio

async def test_unique_constraints(test_session):
    """Проверяем уникальные ограничения в таблице contacts"""
    # Добавляем первый контакт
    contact1 = ContactSchema(name="Unique Test", phone_number="+7777777777")
    test_session.add(contact1)
    await test_session.commit()
    
    # Пытаемся добавить контакт с тем же именем
    contact2 = ContactSchema(name="Unique Test", phone_number="+8888888888")
    test_session.add(contact2)
    
    with pytest.raises(IntegrityError):
        await test_session.commit()
    
    await test_session.rollback()
    
    # Пытаемся добавить контакт с тем же номером телефона
    contact3 = ContactSchema(name="Different Name", phone_number="+7777777777")
    test_session.add(contact3)
    
    with pytest.raises(IntegrityError):
        await test_session.commit()
    
    # Важно: добавляем rollback после второго теста ограничения
    await test_session.rollback()

    
async def test_update_contact(test_session):
    """Тестируем обновление контакта"""
    # Создаем контакт
    contact = ContactSchema(name="Update Test", phone_number="+1212121212")
    test_session.add(contact)
    await test_session.commit()
    await test_session.refresh(contact)
    
    # Обновляем номер телефона
    await test_session.execute(
        update(ContactSchema)
        .where(ContactSchema.name == "Update Test")
        .values(phone_number="+3434343434")
    )
    await test_session.commit()
    
    # Проверяем, что номер обновился
    result = await test_session.execute(
        select(ContactSchema).where(ContactSchema.name == "Update Test")
    )
    updated_contact = result.scalar_one_or_none()
    assert updated_contact is not None
    assert updated_contact.phone_number == "+3434343434"

async def test_delete_contact(test_session):
    """Тестируем удаление контакта"""
    # Создаем контакт
    contact = ContactSchema(name="Delete Test", phone_number="+9876543210")
    test_session.add(contact)
    await test_session.commit()
    
    # Удаляем контакт
    await test_session.execute(
        delete(ContactSchema).where(ContactSchema.name == "Delete Test")
    )
    await test_session.commit()
    
    # Проверяем, что контакт удален
    result = await test_session.execute(
        select(ContactSchema).where(ContactSchema.name == "Delete Test")
    )
    deleted_contact = result.scalar_one_or_none()
    assert deleted_contact is None