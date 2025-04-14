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
    #  paper_id: str = Query(..., description="Document ID for image tracking")
    print(f"Received file",file.filename)
    if not file.filename.endswith('.docx'):
        print(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="File must be a .docx document")
    
    try:
        print(f"Received file: {file.filename}")
        processor = DocxProcessor()
        # processor = DocxProcessor(SCILEDGER_URL, paper_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            html_content = processor.convert(tmp_path)
            return {"html": html_content}
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))