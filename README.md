# DTH Service - SciLedger

**Status: In Development**

A DOCX-to-HTML conversion service with image processing, developed as part of the SciLedger project.

## Technologies Used

### Backend
- **FastAPI** – Modern web framework for APIs
- **python-docx** – DOCX document processing
- **Uvicorn** – High-performance ASGI server
- **python-multipart** – File upload support
- **Requests** – HTTP client for image uploads

### Design Patterns
- **MVC** – Separation between routes, business logic, and processing
- **Dependency Injection** – Flexible configuration via environment variables
- **Error Handling** – Centralized exception handling
- **RESTful API** – Standardized endpoints

## Installation

### Prerequisites
- Python 3.10+
- Git

### Clone the repository
```bash
git clone <repository-url>
cd dth-service
```

### Set up virtual environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Start the server

**Windows:**
```powershell
.\venv\Scripts\activate
uvicorn src.main:app --reload
```

**Linux:**
```bash
source venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Service available at:
- **API:** http://127.0.0.1:8000
- **Docs:** http://127.0.0.1:8000/docs

### Running Tests

**Windows:**
```powershell
pytest tests\test_api.py -v        # Run all tests
pytest tests\test_api.py -v -s     # With console output
```

**Linux:**
```bash
pytest tests/test_api.py -v        # Run all tests
pytest tests/test_api.py -v -s     # With console output
```

## API Endpoints

### Convert DOCX to HTML
```http
POST /api/convert
Content-Type: multipart/form-data

file: document.docx
```

**Response:**
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
│   └── main.py       # Application entry point
├── tests/            # Test files
└── requirements.txt  # Dependencies
```

## Configuration

- **SciLedger URL:** http://localhost:5173
- **DTH Service Port:** 8000

## Dependencies

- fastapi
- python-docx
- uvicorn
- pytest
- requests

## Production Deployment

### Using PM2 (Linux)

1. **Create the deployment script:**
```bash
cat > ~/dth_deploy.sh << 'EOL'
#!/bin/bash

# Navigate to project directory
cd /var/www/dth-service

# Activate virtual environment
source venv/bin/activate

# Pull latest changes
git stash
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Stop existing PM2 process if exists
pm2 delete dth-service || true

# Start with PM2 (localhost only)
pm2 start "venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000" --name "dth-service"

# Save PM2 process list
pm2 save
EOL
```

2. **Make it executable and run:**
```bash
chmod +x ~/dth_deploy.sh
~/dth_deploy.sh
```

3. **Verify deployment:**
```bash
pm2 status
curl http://127.0.0.1:8000/docs
pm2 logs dth-service
```

### Common PM2 commands:
```bash
pm2 restart dth-service    # Restart service
pm2 stop dth-service       # Stop service
pm2 delete dth-service     # Remove service
pm2 logs dth-service       # View logs
pm2 save                   # Save process list
```

### Deployment Notes
- Runs on http://127.0.0.1:8000 (internal only)
- Auto-restart enabled
- Starts automatically on system reboot
- Monitored by PM2

## License

This project is licensed under the MIT License. See the LICENSE file for more details.