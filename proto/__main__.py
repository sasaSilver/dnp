"""
Compile proto files and change internal imports from absolute to relative.
"""
from grpc_tools import protoc

if __name__ == "__main__":
    protoc.main((
        '',
        '-Iproto',
        '--python_out=proto',
        '--grpc_python_out=proto',
        '--mypy_out=proto',
        'proto/phonebook.proto',
    ))
    with open('proto/phonebook_pb2_grpc.py', 'r+') as f:
        content = f.read()
        f.seek(0)
        f.write(content.replace(
            'import phonebook_pb2 as phonebook__pb2',
            'from . import phonebook_pb2 as phonebook__pb2'
        ))