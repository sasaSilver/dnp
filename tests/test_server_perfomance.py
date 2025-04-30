# tests/test_server_performance.py
import pytest
import time
import asyncio
from datetime import datetime
import re
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from proto.phonebook_pb2 import LookupRequest, AddEntryRequest

# Маркер для асинхронных тестов
pytestmark = pytest.mark.asyncio

async def test_server_response_time(grpc_stub):
    """Измеряем время ответа сервера при добавлении и поиске записей"""
    # Подготовка тестовых данных
    test_name = f"Performance Test {datetime.now().timestamp()}"
    test_number = "+7999888777"
    
    # Тест производительности AddEntry
    start_time = time.time()
    add_response = await grpc_stub.AddEntry(
        AddEntryRequest(name=test_name, number=test_number)
    )
    add_time = time.time() - start_time
    
    assert add_response.success is True
    print(f"\nAddEntry response time: {add_time:.4f} seconds")
    assert add_time < 0.5, "AddEntry должен отвечать менее чем за 0.5 секунды"
    
    # Тест производительности Lookup
    start_time = time.time()
    lookup_response = await grpc_stub.Lookup(
        LookupRequest(name=test_name)
    )
    lookup_time = time.time() - start_time
    
    assert lookup_response.number == test_number
    print(f"Lookup response time: {lookup_time:.4f} seconds")
    assert lookup_time < 0.5, "Lookup должен отвечать менее чем за 0.5 секунды"

async def test_parallel_requests_performance(grpc_stub):
    """Измеряем время ответа сервера при параллельных запросах"""
    # Создаем 5 пользователей для тестирования
    test_users = []
    for i in range(5):
        name = f"Parallel Test {i} {datetime.now().timestamp()}"
        number = f"+7{i}00111222"
        test_users.append((name, number))
    
    # Параллельно добавляем пользователей
    start_time = time.time()
    tasks = []
    for name, number in test_users:
        tasks.append(
            grpc_stub.AddEntry(AddEntryRequest(name=name, number=number))
        )
    
    # Ждем выполнения всех запросов
    add_responses = await asyncio.gather(*tasks)
    parallel_add_time = time.time() - start_time
    
    for response in add_responses:
        assert response.success is True
    
    avg_time = parallel_add_time / len(test_users)
    print(f"\nParallel AddEntry total time: {parallel_add_time:.4f} seconds")
    print(f"Average time per request: {avg_time:.4f} seconds")
    
    # Теперь тестируем параллельные запросы поиска
    start_time = time.time()
    lookup_tasks = []
    for name, _ in test_users:
        lookup_tasks.append(
            grpc_stub.Lookup(LookupRequest(name=name))
        )
    
    # Ждем выполнения всех запросов
    lookup_responses = await asyncio.gather(*lookup_tasks)
    parallel_lookup_time = time.time() - start_time
    
    avg_lookup_time = parallel_lookup_time / len(test_users)
    print(f"Parallel Lookup total time: {parallel_lookup_time:.4f} seconds")
    print(f"Average lookup time per request: {avg_lookup_time:.4f} seconds")
    
    assert avg_lookup_time < 0.5, "Среднее время запроса должно быть менее 0.5 секунды"