import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import settings
from services import document_service

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PDF to Markdown Converter",
    description="Convert PDF files to Markdown format using MarkItDown and clean with vLLM",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CleanMarkdownRequest(BaseModel):
    markdown_content: str


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "PDF to Markdown Converter API is running"}


@app.get("/health")
async def health_check():
    """Detailed health check including vLLM connectivity"""
    return await document_service.get_health_status()


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    clean_with_llm: bool = True
):
    """
    Upload PDF file and convert to markdown format
    
    Args:
        file: PDF file to convert
        clean_with_llm: Whether to clean the content with vLLM (default: True)
    
    Returns:
        JSON response with markdown content and metadata
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files are supported"
        )
    
    # Check file size
    max_size = settings.max_file_size_mb * 1024 * 1024
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size too large. Maximum size is {settings.max_file_size_mb}MB"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        logger.info(f"Processing uploaded file: {file.filename} ({len(file_content)} bytes)")
        
        # Process document
        result = await document_service.process_document(
            file_content, file.filename, clean_with_llm
        )
        
        logger.info(f"Successfully processed {file.filename}")
        return JSONResponse(content=result)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/convert-text")
async def convert_text_only(
    file: UploadFile = File(...)
):
    """
    Convert PDF to markdown without LLM cleaning (faster option)
    """
    return await upload_pdf(file, clean_with_llm=False)


@app.post("/clean-markdown")
async def clean_existing_markdown(request: CleanMarkdownRequest):
    """
    Clean existing markdown content using vLLM
    
    Args:
        request: Request containing markdown content to clean
        
    Returns:
        Cleaned markdown content
    """
    if not request.markdown_content.strip():
        raise HTTPException(status_code=400, detail="Markdown content cannot be empty")
    
    try:
        cleaned_content = await document_service.vllm_service.clean_markdown_content(
            request.markdown_content
        )
        return {
            "success": True,
            "original_content": request.markdown_content,
            "cleaned_content": cleaned_content,
            "content_length": len(cleaned_content)
        }
    except Exception as e:
        logger.error(f"Error cleaning markdown: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clean markdown: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    logger.info(f"vLLM service URL: {settings.vllm_base_url}")
    logger.info(f"vLLM model: {settings.vllm_model_name}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    ) 