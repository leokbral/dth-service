import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router as api_router
from .core.docx_processor import DocxProcessor
import uvicorn

app = FastAPI(
    title="DTH Service",
    description="DOCX to HTML conversion service"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the DTH service"}

app.include_router(api_router)

def main():
    if len(sys.argv) != 2:
        print("Uso: python main.py arquivo.docx")
        sys.exit(1)

    try:
        processor = DocxProcessor()
        docx_path = sys.argv[1]
        html_content = processor.convert(docx_path)
        print(html_content)
        
    except Exception as e:
        print(f"Erro: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)