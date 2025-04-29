import grpc
from concurrent import futures
import phonebook_pb2
import phonebook_pb2_grpc
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class PhonebookService(phonebook_pb2_grpc.PhonebookServicer):
    def __init__(self):
        self.entries: dict[str, tuple[str, str]] = {}
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        print(
            "SERVER PUBLIC KEY:", self.public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            ).hex()
        )

    def AddEntry(self, request, context):
        if request.name in self.entries:
            return phonebook_pb2.AddEntryResponse(
                success=False,
                message="Name already exists"
            )
        
        self.entries[request.name] = request.number
        return phonebook_pb2.AddEntryResponse(
            success=True,
            message="Entry added"
        )

    def Lookup(self, request, context):
        if request.name not in self.entries:
            context.abort(grpc.StatusCode.NOT_FOUND, "Name not found")
            
        number = self.entries[request.name]
        
        data_to_sign = f"{request.name}:{number}".encode()
        signature = self.private_key.sign(data_to_sign)
        
        return phonebook_pb2.LookupResponse(
            number=number,
            signature=signature
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    phonebook_pb2_grpc.add_PhonebookServicer_to_server(
        PhonebookService(), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Server running on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    import time
    serve()