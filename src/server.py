import asyncio
import datetime
import functools

import grpc
from grpc import aio
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from proto import phonebook_pb2_grpc
from proto.phonebook_pb2 import (
    LookupRequest, LookupResponse,
    AddEntryRequest, AddEntryResponse
)
from models.contact import ContactSchema
from .core import get_db, create_tables

"""
TODO add service layer with database querying & logic
"""

class PhonebookService(phonebook_pb2_grpc.PhonebookServicer):
    def __init__(self) -> None:
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        print(
            "SERVER PUBLIC KEY:", self.public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            ).hex()
        )
    
    async def AddEntry(
        self,
        request: AddEntryRequest,
        context: aio.ServicerContext
    ) -> AddEntryResponse:
        # Используем асинхронный генератор get_db для получения сессии
        db_gen = get_db()
        session = await anext(db_gen)
        
        try:
            # Проверяем, существует ли уже запись с таким именем
            existing_entry = await session.execute(
                select(ContactSchema).where(ContactSchema.name == request.name)
            )
            if existing_entry.scalar_one_or_none():
                return AddEntryResponse(
                    success=False,
                    message="Name already exists"
                )
            
            # Создаем новую запись
            new_contact = ContactSchema(
                name=request.name,
                phone_number=request.number
            )
            session.add(new_contact)
            await session.commit()
            # Обновляем объект, чтобы получить ID
            await session.refresh(new_contact)
            
            return AddEntryResponse(
                success=True,
                id=new_contact.id,
                message="Entry added"
            )
        except Exception as e:
            await session.rollback()
            return AddEntryResponse(
                success=False,
                message=f"Error: {str(e)}"
            )
        finally:
            # Закрываем генератор
            try:
                await db_gen.aclose()
            except Exception:
                pass
    
    async def Lookup(
        self,
        request: LookupRequest,
        context: aio.ServicerContext
    ) -> LookupResponse:
        # Используем асинхронный генератор get_db для получения сессии
        db_gen = get_db()
        session = await anext(db_gen)
        
        try:
            # Ищем контакт в базе данных
            result = await session.execute(
                select(ContactSchema).where(ContactSchema.name == request.name)
            )
            contact = result.scalar_one_or_none()
            
            if not contact:
                await context.abort(grpc.StatusCode.NOT_FOUND, "Name not found")
                
            # Формируем ответ
            number: str = contact.phone_number
            time = datetime.datetime.now().isoformat()
            data_to_sign: bytes = f"{request.name}:{number}:{time}".encode()
            signature: bytes = self.private_key.sign(data_to_sign)
            
            return LookupResponse(
                number=number,
                time=time,
                signature=signature
            )
        finally:
            # Закрываем генератор
            try:
                await db_gen.aclose()
            except Exception:
                pass

async def serve():
    # Создаем таблицы при необходимости
    await create_tables()
    
    # Запускаем сервер
    server = aio.server() 
    phonebook_pb2_grpc.add_PhonebookServicer_to_server(
        PhonebookService(), server
    )
    server.add_insecure_port("[::]:50051")
    await server.start()
    print("Server running on port 50051")
    
    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        await server.stop(grace=5)

if __name__ == "__main__":
    asyncio.run(serve())