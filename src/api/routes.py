from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from ..core.docx_processor import DocxProcessor
import tempfile
import os
# const formData = new FormData();
# formData.append('file', imageFile);

# const response = await fetch('/api/images/upload', {
#     method: 'POST',
#     body: formData
# });

# const result = await response.json();
# // result.id will contain the image ID if successful
router = APIRouter()

SCILEDGER_URL = "http://localhost:3000"  # Update with actual Sciledger URL

@router.post("/api/convert")
async def convert_docx(
    file: UploadFile = File(...)
):
    print(f"Received file: {file.filename}")
    
    if not file.filename.endswith('.docx'):
        print(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="File must be a .docx document")
    
    try:
        processor = DocxProcessor()
        
        # Create temp file with debug info
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            content = await file.read()
            print(f"File content size: {len(content)} bytes")
            tmp.write(content)
            tmp_path = tmp.name
            print(f"Temporary file created at: {tmp_path}")
        
        try:
            # Convert with detailed logging
            print(f"Starting conversion of: {tmp_path}")
            html_content = processor.convert(tmp_path)
            print(f"Conversion completed. HTML length: {len(html_content)}")
            return {"html": html_content}
            
        except Exception as conv_error:
            print(f"Conversion error: {str(conv_error)}")
            print(f"Error type: {type(conv_error)}")
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(conv_error)}")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                print(f"Temporary file removed: {tmp_path}")
                
    except Exception as e:
        print(f"Processing error: {str(e)}")
        print(f"Error type: {type(e)}")
        raise HTTPException(status_code=400, detail=str(e))