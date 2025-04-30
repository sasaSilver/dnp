## ✅ How to Run the Project

### 1. 📦 Install Dependencies
Before running the project, make sure you have **Python 3.11+** installed. Create a virtual environment and install the dependencies:

```bash
python -m venv venv
source venv/bin/activate  
pip install -e . 
```

## 2. 📁 Compile .proto File
Generate Python code from the phonebook.proto file:

```bash
python -m proto
```
This will generate phonebook_pb2.py and phonebook_pb2_grpc.py with correct relative imports.

## 3. Create your `.env` file. Consult `.env.example`


## 4. 🚀 Start the Server

```bash

python -m src.server
```
The gRPC server will listen on localhost:50051.

## 🧪 Run Client Tests (Terminal)

Set environment variable `TESTING` to 1 in `.env`

Execute test interactions with the server:

```bash
python -m src.test_server
```
- Tests include:

- Adding new contacts

- Handling duplicates

- Performing lookups
- Verifying digital signatures

- Timing responses

💡 Streamlit Web Interface

Located in `front` branch.

Repeat steps 1-3 for the server.

```bash
python -m streamlit run src/client.py
```
The interface will open in your browser.
