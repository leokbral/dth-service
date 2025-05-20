import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app

client = TestClient(app)

# Test data directory
TEST_DIR = Path(__file__).parent / "test_data"
TEST_DOCX = TEST_DIR / "test.docx"

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the DTH service"}

def test_convert_endpoint_with_valid_docx():
    if not TEST_DOCX.exists():
        pytest.skip("Test DOCX file not found")
    
    print(f"\nTest file exists: {TEST_DOCX.exists()}")
    print(f"Test file size: {TEST_DOCX.stat().st_size} bytes")
    
    with open(TEST_DOCX, "rb") as f:
        content = f.read()
        print(f"File content length: {len(content)} bytes")
        files = {"file": ("test.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        
        try:
            response = client.post("/api/convert", files=files)
            print(f"\nDebug - Response details:")
            print(f"Status: {response.status_code}")
            print(f"Headers: {response.headers}")
            print(f"Content: {response.text}")  # Using .text instead of .content for readable output
            
            if response.status_code != 200:
                error_detail = response.json().get('detail', 'No detail provided')
                print(f"Error detail: {error_detail}")
            
        except Exception as e:
            print(f"Request failed: {str(e)}")
            raise
        
    assert response.status_code == 200, f"Conversion failed: {response.text}"
    result = response.json()
    assert "html" in result, "Response missing 'html' field"
    
    html_content = result["html"]
    assert html_content, "HTML content should not be empty"

def test_convert_endpoint_with_invalid_file():
    files = {"file": ("test.txt", b"invalid content", "text/plain")}
    response = client.post("/api/convert", files=files)
    assert response.status_code == 400