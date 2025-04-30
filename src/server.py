import asyncio
import datetime
import logging

import grpc
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from proto import phonebook_pb2_grpc
from proto.phonebook_pb2 import (
    LookupRequest, LookupResponse,
    AddEntryRequest, AddEntryResponse,
    GetKeyRequest, GetKeyResponse
)
from .models.contact import ContactSchema
from .core import inject_session, create_tables, engine
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SERVER")

class PhonebookService(phonebook_pb2_grpc.PhonebookServicer):
    def __init__(self) -> None:
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

    async def GetKey(
        self,
        request: GetKeyRequest,
        context: grpc.aio.ServicerContext
    ) -> GetKeyResponse:
        key = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        ).hex()
        logger.info("Key request")
        return GetKeyResponse(key=key)

    @inject_session
    async def AddEntry(
        self,
        request: AddEntryRequest,
        context: grpc.aio.ServicerContext,
        db: AsyncSession,
    ) -> AddEntryResponse:
        existing_entry = await db.execute(
            select(ContactSchema).where(ContactSchema.name == request.name)
        )
        if existing_entry.scalar_one_or_none():
            return AddEntryResponse(
                success=False,
                message="Name already exists"
            )

        new_contact = ContactSchema(
            name=request.name,
            phone_number=request.number
        )
        db.add(new_contact)
        await db.flush()
        await db.refresh(new_contact)

        logger.info(f"Add entry: {request.name}:{request.number}")
        
        return AddEntryResponse(
            success=True,
            message="Entry added"
        )

    @inject_session
    async def Lookup(
        self,
        request: LookupRequest,
        context: grpc.aio.ServicerContext,
        db: AsyncSession,
    ) -> LookupResponse:
        result = await db.execute(
            select(ContactSchema).where(ContactSchema.name == request.name)
        )
        contact = result.scalar_one_or_none()

        if not contact:
            return LookupResponse(
                success=False,
                number="",
                time="",
                signature=""
            )

        number: str = contact.phone_number
        time = datetime.datetime.now().isoformat()
        data_to_sign: bytes = f"{request.name}:{number}:{time}".encode()
        signature: bytes = self.private_key.sign(data_to_sign)

        logger.info(f"Look up: {request.name}:{number}")

        return LookupResponse(
            success=True,
            number=number,
            time=time,
            signature=signature
        )

async def serve():
    await create_tables()

    server = grpc.aio.server()
    phonebook_pb2_grpc.add_PhonebookServicer_to_server(
        PhonebookService(), server
    )
    server.add_insecure_port(settings.server_addr)
    await server.start()
    print("Server running on port 50051")

    try:
        await server.wait_for_termination()
    finally:
        engine.dispose()
        await server.stop(grace=5)

if __name__ == "__main__":
    asyncio.run(serve())
