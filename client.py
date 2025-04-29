import streamlit as st
import grpc
import phonebook_pb2
import phonebook_pb2_grpc
from cryptography.hazmat.primitives.asymmetric import ed25519

SERVER_ADDRESS = "localhost:50051"
PUBKEY = ed25519.Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(st.secrets["SERVER_PUBLIC_KEY"])
        )

def verify_signature(name: str, number: str, signature: bytes):
    try:
        signed_data = f"{name}:{number}".encode()
        PUBKEY.verify(signature, signed_data)
        return True
    except Exception as e:
        st.error(f"Verification failed: {str(e)}")
        return False

def main():
    st.title("🔍 Phonebook Lookup (gRPC)")
    
    channel = grpc.insecure_channel(SERVER_ADDRESS)
    stub = phonebook_pb2_grpc.PhonebookStub(channel)

    st.header("Lookup Entry")
    name = st.text_input("Name")
    if st.button("Find"):
        if name:
            try:
                response = stub.Lookup(phonebook_pb2.LookupRequest(name=name))
                valid = verify_signature(name, response.number, response.signature)
                if valid:
                    st.success("✅ Valid signature!")
                else:
                    st.error("❌ Invalid signature")
                st.success(f"Number: {response.number}")
                st.write("Signature valid: ✅" if valid else "❌ Invalid signature!")
            except grpc.RpcError as e:
                st.error(f"Error: {e.details()}")
        else:
            st.warning("Please enter a name")

    st.header("Add New Entry")
    with st.form("add_form"):
        new_name = st.text_input("Name")
        new_number = st.text_input("Phone Number")
        if st.form_submit_button("Add"):
            if new_name and new_number:
                try:
                    response = stub.AddEntry(
                        phonebook_pb2.AddEntryRequest(
                            name=new_name,
                            number=new_number
                        ))
                    st.success(response.message)
                except grpc.RpcError as e:
                    st.error(f"Error: {e.details()}")
            else:
                st.error("Both fields are required")

if __name__ == "__main__":
    main()