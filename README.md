# dth-service README.md

# DTH Service
Convert DOCX documents to HTML with image processing support.

## Prerequisites
- Python 3.10+
- Windows OS
- Git

## Installation

1. **Clone repository**
```powershell
git clone <repository-url>
cd dth-service
```

2. **Set up virtual environment**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

3. **Install dependencies**
```powershell
pip install -r requirements.txt
```

## Usage

### Start Server
```powershell
.\venv\Scripts\activate
uvicorn src.main:app --reload
```
Service runs at:
- API: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`

### Run Tests
```powershell
pytest tests\test_api.py -v        # Run all tests
pytest tests\test_api.py -v -s     # With console output
```

## API Endpoints

### Convert DOCX to HTML
```http
POST /api/convert
Content-Type: multipart/form-data

file: document.docx
```

Response:
```json
{
  "html": "<converted html content>"
}
```

## Project Structure
```
dth-service/
├── src/
│   ├── api/          # API routes
│   ├── core/         # Business logic
│   └── main.py      # Entry point
├── tests/           # Test files
└── requirements.txt # Dependencies
```

## Configuration
- Sciledger URL: `http://localhost:5173` 
- DTH Service port: `8000`

## Dependencies
- fastapi
- python-docx
- uvicorn
- pytest
- requests

## License

This project is licensed under the MIT License. See the LICENSE file for details.