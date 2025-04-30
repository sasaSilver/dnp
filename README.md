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

### 3.5 Make sure server is already running.

## 4. Launch a client

 ```bash
python -m streamlit run src/client.py
```
The interface will open in your browser.