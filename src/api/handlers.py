from fastapi import APIRouter, HTTPException
from src.core.docx_processor import DocxProcessor

router = APIRouter()

@router.post("/process-docx/")
async def process_docx(file: bytes):
    try:
        processor = DocxProcessor()
        html_output = processor.process_docx(file)
        return {"html": html_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))