import asyncio
import grpc
from proto import phonebook_pb2_grpc
from proto.phonebook_pb2 import LookupRequest, AddEntryRequest

async def run_client():
    # Создаем канал и клиент
    channel = grpc.aio.insecure_channel('localhost:50051')
    stub = phonebook_pb2_grpc.PhonebookStub(channel)
    
    # Тестируем добавление записи
    try:
        # Добавляем первую запись
        add_response = await stub.AddEntry(
            AddEntryRequest(name="John Doe", number="+1234567890")
        )
        print("AddEntry response 1:", add_response)
        
        # Пробуем добавить дубликат
        add_duplicate = await stub.AddEntry(
            AddEntryRequest(name="John Doe", number="+9999999999")
        )
        print("AddEntry duplicate:", add_duplicate)
        
        # Добавляем вторую запись
        add_response2 = await stub.AddEntry(
            AddEntryRequest(name="Jane Smith", number="+0987654321")
        )
        print("AddEntry response 2:", add_response2)
        
        # Ищем существующий контакт
        lookup_response = await stub.Lookup(LookupRequest(name="John Doe"))
        print("Lookup response:", lookup_response.number)
        print("Signature:", lookup_response.signature.hex())
        
        # Ищем несуществующий контакт
        try:
            await stub.Lookup(LookupRequest(name="Non Existent"))
            print("Lookup for non-existent contact unexpectedly succeeded")
        except grpc.RpcError as e:
            print(f"Lookup for non-existent contact correctly failed: {e.details()}")
    
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Закрываем канал
        await channel.close()

if __name__ == "__main__":
    asyncio.run(run_client())