# dth-service README.md

# DTH Service
Convert DOCX documents to HTML with image processing support.

## Prerequisites
- Python 3.10+
- Git

## Installation

1. **Clone repository**
```bash
git clone <repository-url>
cd dth-service
```

2. **Set up virtual environment**

Windows:
```powershell
python -m venv venv
.\venv\Scripts\activate
```

Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## Usage

### Start Server

Windows:
```powershell
.\venv\Scripts\activate
uvicorn src.main:app --reload
```

Linux:
```bash
source venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Service runs at:
- API: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`

### Run Tests

Windows:
```powershell
pytest tests\test_api.py -v        # Run all tests
pytest tests\test_api.py -v -s     # With console output
```

Linux:
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

## Production Deployment

### Using PM2 (Linux)

1. **Create deployment script**:
```bash
cat > ~/dth_deploy.sh << 'EOL'
#!/bin/bash

# Navigate to project directory
cd /var/www/dth-service

# Activate virtual environment
source venv/bin/activate

# Update from git
git stash
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Stop existing PM2 process if exists
pm2 delete dth-service || true

# Start with PM2 - localhost only
pm2 start "venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000" --name "dth-service"

# Save PM2 process list
pm2 save
EOL
```

2. **Make script executable and deploy**:
```bash
chmod +x ~/dth_deploy.sh
~/dth_deploy.sh
```

3. **Verify deployment**:
```bash
# Check PM2 status
pm2 status

# Test API
curl http://127.0.0.1:8000/docs

# View logs
pm2 logs dth-service
```

4. **Common PM2 Commands**:
```bash
pm2 restart dth-service    # Restart service
pm2 stop dth-service      # Stop service
pm2 delete dth-service    # Remove service
pm2 logs dth-service      # View logs
pm2 save                  # Save process list
```

Service Configuration:
- Internal Access Only: `http://127.0.0.1:8000`
- Auto-restart enabled
- Starts automatically on system reboot
- Process monitored by PM2