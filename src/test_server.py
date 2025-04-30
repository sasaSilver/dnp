import time
from concurrent import futures

import grpc
from cryptography.hazmat.primitives.asymmetric import ed25519

from proto import phonebook_pb2_grpc
from proto.phonebook_pb2 import (
    LookupRequest, LookupResponse,
    AddEntryRequest, AddEntryResponse,
    GetKeyRequest, GetKeyResponse
)

channel = grpc.insecure_channel('localhost:50051')
stub = phonebook_pb2_grpc.PhonebookStub(channel)

def get_key():
    key_reponse: GetKeyResponse = stub.GetKey(GetKeyRequest())
    return ed25519.Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(key_reponse.key)
    )

public_key = get_key()

def verify_signature(name: str, number: str, timestamp: str, signature: bytes) -> bool:
    signed_data = f"{name}:{number}:{timestamp}".encode()
    try:
        public_key.verify(signature, signed_data)
        return True
    except:
        return False

def test_add() -> tuple[float, float]:
    name = "test"
    number = "1234567890"
    
    add_start = time.perf_counter()
    add_response: AddEntryResponse = stub.AddEntry(AddEntryRequest(name=name, number=number))
    add_time = (time.perf_counter() - add_start) * 1000
    
    assert add_response.success, f"Unable to add a number with name {name}"
    
    lookup_start = time.perf_counter()
    lookup_response: LookupResponse = stub.Lookup(LookupRequest(name=name))
    lookup_time = (time.perf_counter() - lookup_start) * 1000
    
    assert lookup_response.success, f"Unable to retreive a number for name {name}"
    
    assert lookup_response.number == number
    assert verify_signature(
        name, 
        number, 
        lookup_response.time, 
        lookup_response.signature
    ), "Signature verification failed"
    
    return add_time, lookup_time

def test_duplicate() -> float:
    name = "duplicate_test"
    
    start = time.perf_counter()
    stub.AddEntry(AddEntryRequest(name=name, number="111"))
    response: AddEntryResponse = stub.AddEntry(AddEntryRequest(name=name, number="222"))
    elapsed = (time.perf_counter() - start) * 1000
    
    assert not response.success, "Should reject duplicate names"
    return elapsed

def test_parallel() -> tuple[float, float]:
    def _add(i: int):
        return stub.AddEntry(AddEntryRequest(name=str(i), number=str(i)))
    
    def _lookup(i: int):
        return stub.Lookup(LookupRequest(name=str(i)))
    
    add_start = time.perf_counter()
    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        add_responses: list[AddEntryResponse] = list(executor.map(_add, range(10)))
    add_time = (time.perf_counter() - add_start) * 1000
    
    lookup_start = time.perf_counter()
    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        lookup_responses: list[LookupResponse] = list(executor.map(_lookup, range(10)))
    lookup_time = (time.perf_counter() - lookup_start) * 1000
    
    assert all(r.success for r in add_responses), "Not all insertions were successful"
    assert all(r.success for r in lookup_responses), "Not all lookups were successful"
    assert all(verify_signature(
        str(i), str(i), r.time, r.signature
    ) for i, r in enumerate(lookup_responses)), "Not all signatures are valid"
    
    return add_time, lookup_time

def run_tests():
    print("=== Starting Tests ===")
    
    add_time, lookup_time = test_add()
    print(f"✓ test_add passed - Add: {add_time:.2f}ms, Lookup: {lookup_time:.2f}ms")
    
    dup_time = test_duplicate()
    print(f"✓ test_duplicate passed - {dup_time:.2f}ms")
    
    parallel_add, parallel_lookup = test_parallel()
    print(f"✓ test_parallel passed - Adds: {parallel_add:.2f}ms, Lookups: {parallel_lookup:.2f}ms")
    
    print("\n=== Test Summary ===")
    print(f"Single Add: {add_time:.2f}ms")
    print(f"Single Lookup: {lookup_time:.2f}ms")
    print(f"Duplicate Check: {dup_time:.2f}ms")
    print(f"Parallel Adds (10): {parallel_add:.2f}ms")
    print(f"Parallel Lookups (10): {parallel_lookup:.2f}ms")

if __name__ == "__main__":
    run_tests()