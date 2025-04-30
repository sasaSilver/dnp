import asyncio

import grpc
from grpc import aio
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from sqlalchemy.ext.asyncio import AsyncSession

from proto import phonebook_pb2_grpc
from proto.phonebook_pb2 import (
    LookupRequest, LookupResponse,
    AddEntryRequest, AddEntryResponse
)

"""
TODO add service layer with database querying & logic
"""

class PhonebookService(phonebook_pb2_grpc.PhonebookServicer):
    def __init__(self) -> None:
        self.entries: dict[str, str] = {}
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
        context: aio.ServicerContext,
        db: AsyncSession
    ) -> AddEntryResponse:
        if request.name in self.entries:
            return AddEntryResponse(
                success=False,
                message="Name already exists"
            )
        
        self.entries[request.name] = request.number
        return AddEntryResponse(
            success=True,
            id=0, # change to added entry's id
            message="Entry added"
        )
    
    async def Lookup(
        self,
        request: LookupRequest,
        context: aio.ServicerContext,
        db: AsyncSession
    ) -> LookupResponse:
        if request.name not in self.entries:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Name not found")
            
        number: str = self.entries[request.name]
        data_to_sign: bytes = f"{request.name}:{number}".encode()
        signature: bytes = self.private_key.sign(data_to_sign)
        
        return LookupResponse(
            number=number,
            signature=signature
        )

async def serve():
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