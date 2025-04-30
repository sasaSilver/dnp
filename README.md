## ✅ How to Run the Project

### 1. 📦 Install Dependencies
Before running the project, make sure you have **Python 3.11+** installed. Create a virtual environment and install the dependencies:

```bash
python -m venv venv
source venv/bin/activate  
pip install -e . 
```

2. 📁 Compile .proto File
Generate Python code from the phonebook.proto file:

```bash
python -m proto
```
This will generate phonebook_pb2.py and phonebook_pb2_grpc.py with correct relative imports.

3. 🚀 Start the Server

```bash

python -m src.server
```
The gRPC server will listen on localhost:50051.

5. 🧪 Run Client Tests (Terminal)
Execute test interactions with the server:

```bash
python -m tests.test_server
```
- Tests include:

- Adding new contacts

- Handling duplicates

- Performing lookups
- Verifying digital signatures

- Timing responses

6. 💡 Streamlit Web Interface

```bash
python -m streamlit run src/client.py
```
The interface will open in your browser.
