import streamlit as st
import grpc
from cryptography.hazmat.primitives.asymmetric import ed25519

import proto.phonebook_pb2_grpc as phonebook_pb2_grpc
from proto.phonebook_pb2 import (
    LookupRequest, LookupResponse,
    AddEntryRequest, AddEntryResponse,
    GetKeyRequest, GetKeyResponse
)

SERVER_ADDRESS = "localhost:50051"
channel = grpc.insecure_channel(SERVER_ADDRESS)
stub = phonebook_pb2_grpc.PhonebookStub(channel)

def get_key():
    key_reponse: GetKeyResponse = stub.GetKey(GetKeyRequest())
    return ed25519.Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(key_reponse.key)
    )

PUBKEY = get_key()

def verify_signature(name: str, number: str, time: str, signature: bytes):
    signed_data = f"{name}:{number}:{time}".encode()
    try:
        PUBKEY.verify(signature, signed_data)
    except:
        st.toast(f"Failed to verify number for {name}!",icon="🚨")
        return False
    return True

def main():
    st.title("🔍 Phonebook")
    
    lookup_tab, add_tab = st.tabs(["Lookup", "Add"])
    
    lookup_tab.header("Look up a number")
    name = lookup_tab.text_input("Name", key="lookup_name")
    if lookup_tab.button("Find"):
        if name:
            try:
                lookup_response: LookupResponse = stub.Lookup(LookupRequest(name=name))
                valid = verify_signature(name, lookup_response.number, lookup_response.time, lookup_response.signature)
                if valid:
                    lookup_tab.badge("Valid signature!", color="green", icon="✅")
                else:
                    lookup_tab.badge("Invalid signature", color="red", icon="❌")
                lookup_tab.success(f"Number: {lookup_response.number}")
            except grpc.RpcError as e:
                st.toast(f"Error: {e}", icon="🚨")
        else:
            lookup_tab.warning("Please enter a name")

    add_tab.header("Add a number")
    add_form = add_tab.form("add_number")
    new_name = add_form.text_input("Name", key="add_name")
    new_number = add_form.text_input("Phone Number", key="add_number")
    if add_form.form_submit_button("Add"):
        if new_name and new_number:
            try:
                add_reponse: AddEntryResponse = stub.AddEntry(
                    AddEntryRequest(
                        name=new_name,
                        number=new_number
                    ))
                add_form.success(add_reponse.message)
            except grpc.RpcError as e:
                st.toast(f"Error: {e}", icon="🚨")
        else:
            st.toast("Both fields are required", icon="🚨")

if __name__ == "__main__":
    main()