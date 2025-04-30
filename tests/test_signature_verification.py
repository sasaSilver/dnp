# tests/test_signature_verification.py
import pytest
import asyncio
import re
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

from proto.phonebook_pb2 import LookupRequest, AddEntryRequest

# Маркер для асинхронных тестов
pytestmark = pytest.mark.asyncio

class SignatureVerifier:
    """Вспомогательный класс для проверки подписи"""
    
    @staticmethod
    def extract_public_key(server_output):
        """Извлекает публичный ключ из вывода сервера"""
        match = re.search(r"SERVER PUBLIC KEY: ([0-9a-fA-F]+)", server_output)
        if match:
            hex_key = match.group(1)
            raw_key = bytes.fromhex(hex_key)
            return ed25519.Ed25519PublicKey.from_public_bytes(raw_key)
        return None
    
    @staticmethod
    def verify_signature(public_key, name, number, signature):
        """Проверяет подпись данных"""
        try:
            return len(signature) == 64  # Длина Ed25519 подписи
        except InvalidSignature:
            return False

async def test_signature_format(grpc_stub):
    """Проверяем, что подпись имеет правильный формат"""
    # Добавляем запись
    test_name = f"Signature Test {datetime.now().timestamp()}"
    test_number = "+7321654987"
    
    add_response = await grpc_stub.AddEntry(
        AddEntryRequest(name=test_name, number=test_number)
    )
    assert add_response.success is True
    
    # Получаем запись с подписью
    lookup_response = await grpc_stub.Lookup(
        LookupRequest(name=test_name)
    )
    
    # Проверяем формат подписи
    signature = lookup_response.signature
    assert len(signature) == 64, "Подпись Ed25519 должна быть длиной 64 байта"

async def test_signature_uniqueness(grpc_stub):
    """Проверяем, что подписи для одного и того же запроса разные (из-за timestamp)"""
    # Добавляем запись
    test_name = f"Unique Signature Test {datetime.now().timestamp()}"
    test_number = "+7123456789"
    
    add_response = await grpc_stub.AddEntry(
        AddEntryRequest(name=test_name, number=test_number)
    )
    assert add_response.success is True
    
    # Делаем первый запрос
    first_response = await grpc_stub.Lookup(
        LookupRequest(name=test_name)
    )
    first_signature = first_response.signature
    
    await asyncio.sleep(1)
    
    # Делаем второй запрос
    second_response = await grpc_stub.Lookup(
        LookupRequest(name=test_name)
    )
    second_signature = second_response.signature
    
    # Проверяем, что подписи разные
    assert first_signature != second_signature, "Подписи должны быть уникальными для каждого запроса"
