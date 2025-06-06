import logging
import atexit
import base64
import urllib.parse
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import json

from config import settings
from services import document_service
from vllm_manager import vllm_manager

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


def encode_filename_for_header(filename: str) -> str:
    """
    Encode filename for HTTP header (must be latin-1 compatible)
    
    For Chinese/Unicode filenames, we use URL encoding which is latin-1 safe
    """
    try:
        # First try: if filename is already latin-1 compatible, use it directly
        filename.encode('latin-1')
        return filename
    except UnicodeEncodeError:
        # Second approach: URL encode the filename (RFC 3986)
        # This converts Chinese characters to %XX format which is latin-1 safe
        encoded = urllib.parse.quote(filename, safe='')
        return encoded


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting PDF to Markdown Converter Backend...")
    
    # Start vLLM service if auto-start is enabled
    if settings.vllm_auto_start:
        logger.info("Auto-starting vLLM service...")
        success = await vllm_manager.start_vllm_service()
        if success:
            logger.info("vLLM service started successfully")
        else:
            logger.warning("Failed to start vLLM service - continuing without it")
    
    yield
    
    # Shutdown
    logger.info("Shutting down backend services...")
    await vllm_manager.stop_vllm_service()
    logger.info("Backend shutdown complete")


app = FastAPI(
    title="PDF to Markdown Converter",
    description="Convert PDF files to Markdown format using MarkItDown and clean with vLLM",
    version="1.0.0",
    lifespan=lifespan
)

# Register shutdown handler for non-graceful exits
atexit.register(lambda: logger.info("Process exiting..."))

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


class VLLMControlRequest(BaseModel):
    model_name: str = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "PDF to Markdown Converter API is running"}


@app.get("/health")
async def health_check():
    """Detailed health check including vLLM connectivity"""
    health_status = await document_service.get_health_status()
    
    # Add vLLM process status
    vllm_status = vllm_manager.get_vllm_status()
    health_status["vllm_process"] = vllm_status
    
    return health_status


@app.get("/vllm/status")
async def get_vllm_status():
    """Get detailed vLLM service status"""
    status = vllm_manager.get_vllm_status()
    status["service_responsive"] = await vllm_manager._is_vllm_running()
    return status


@app.post("/vllm/start")
async def start_vllm_service(request: VLLMControlRequest = None):
    """Start vLLM service"""
    model_name = request.model_name if request else None
    
    logger.info(f"Manual start requested for vLLM service (model: {model_name or 'default'})")
    success = await vllm_manager.start_vllm_service(model_name)
    
    return {
        "success": success,
        "message": "vLLM service started successfully" if success else "Failed to start vLLM service",
        "status": vllm_manager.get_vllm_status()
    }


@app.post("/vllm/stop")
async def stop_vllm_service():
    """Stop vLLM service"""
    logger.info("Manual stop requested for vLLM service")
    success = await vllm_manager.stop_vllm_service()
    
    return {
        "success": success,
        "message": "vLLM service stopped successfully" if success else "Failed to stop vLLM service"
    }


@app.post("/vllm/restart")
async def restart_vllm_service(request: VLLMControlRequest = None):
    """Restart vLLM service"""
    model_name = request.model_name if request else None
    
    logger.info(f"Manual restart requested for vLLM service (model: {model_name or 'default'})")
    success = await vllm_manager.restart_vllm_service(model_name)
    
    return {
        "success": success,
        "message": "vLLM service restarted successfully" if success else "Failed to restart vLLM service",
        "status": vllm_manager.get_vllm_status()
    }


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
    
    # Check if vLLM is needed and available
    if clean_with_llm and not await vllm_manager._is_vllm_running():
        logger.warning("vLLM cleaning requested but service is not running")
        if settings.vllm_auto_start:
            logger.info("Attempting to start vLLM service...")
            success = await vllm_manager.start_vllm_service()
            if not success:
                raise HTTPException(
                    status_code=503,
                    detail="vLLM service is not available and failed to start. Try again or use convert-text endpoint."
                )
        else:
            raise HTTPException(
                status_code=503,
                detail="vLLM service is not available. Use convert-text endpoint for basic conversion."
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
    
    # Check if vLLM is available
    if not await vllm_manager._is_vllm_running():
        if settings.vllm_auto_start:
            logger.info("Starting vLLM service for markdown cleaning...")
            success = await vllm_manager.start_vllm_service()
            if not success:
                raise HTTPException(
                    status_code=503,
                    detail="vLLM service is not available and failed to start"
                )
        else:
            raise HTTPException(
                status_code=503,
                detail="vLLM service is not available"
            )
    
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


@app.post("/clean-markdown-stream")
async def clean_existing_markdown_stream(request: CleanMarkdownRequest):
    """
    Clean existing markdown content using vLLM with streaming response
    
    Args:
        request: Request containing markdown content to clean
        
    Returns:
        Streaming response with cleaned markdown content token by token
    """
    if not request.markdown_content.strip():
        raise HTTPException(status_code=400, detail="Markdown content cannot be empty")
    
    # Check if vLLM is available
    if not await vllm_manager._is_vllm_running():
        if settings.vllm_auto_start:
            logger.info("Starting vLLM service for markdown cleaning...")
            success = await vllm_manager.start_vllm_service()
            if not success:
                raise HTTPException(
                    status_code=503,
                    detail="vLLM service is not available and failed to start"
                )
        else:
            raise HTTPException(
                status_code=503,
                detail="vLLM service is not available"
            )
    
    # Use the sync generator directly without async wrapper
    def generate_stream():
        """Generate streaming response - use sync function"""
        try:
            logger.info("Starting streaming response generation...")
            
            # Get the sync generator from the service
            generator = document_service.vllm_service.clean_markdown_content_stream(
                request.markdown_content
            )
            
            token_count = 0
            for token in generator:  # Sync iteration
                token_count += 1
                logger.debug(f"FastAPI yielding token {token_count}: {repr(token[:20])}")
                yield token
                
            logger.info(f"FastAPI streaming completed with {token_count} tokens")
            
        except Exception as stream_error:
            logger.error(f"Error in FastAPI stream generation: {stream_error}")
            yield f"\n\n[ERROR: {str(stream_error)}]"
            raise
    
    try:
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain; charset=utf-8",  # Explicitly set UTF-8 charset
            headers={
                "X-Content-Type": "streaming",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Transfer-Encoding": "chunked"  # Ensure chunked encoding
            }
        )
    except Exception as e:
        logger.error(f"Error creating streaming response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create streaming response: {str(e)}")


@app.post("/upload-stream")
async def upload_pdf_stream(
    file: UploadFile = File(...)
):
    """
    Upload PDF file, convert to markdown, and clean with streaming LLM response
    
    Args:
        file: PDF file to convert
    
    Returns:
        Streaming response with cleaned markdown content token by token
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
    
    # Check if vLLM is available
    if not await vllm_manager._is_vllm_running():
        if settings.vllm_auto_start:
            logger.info("Attempting to start vLLM service...")
            success = await vllm_manager.start_vllm_service()
            if not success:
                raise HTTPException(
                    status_code=503,
                    detail="vLLM service is not available and failed to start."
                )
        else:
            raise HTTPException(
                status_code=503,
                detail="vLLM service is not available."
            )
    
    try:
        # Read file content
        file_content = await file.read()
        logger.info(f"Processing uploaded file for streaming: {file.filename} ({len(file_content)} bytes)")
        
        # Convert PDF to markdown first (non-streaming) - using the correct attribute
        raw_markdown = await document_service.pdf_service.convert_pdf_to_markdown(
            file_content, file.filename
        )
        
        logger.info(f"PDF converted to markdown, starting streaming cleanup...")
        
        def generate_stream():
            """Generate streaming response with PDF metadata header"""
            try:
                # Send metadata as first chunk (JSON format) - ensure UTF-8 encoding
                metadata = {
                    "filename": file.filename,
                    "file_size_bytes": len(file_content),
                    "raw_content_length": len(raw_markdown)
                }
                # Ensure proper JSON serialization with UTF-8 support
                metadata_json = json.dumps(metadata, ensure_ascii=False)
                yield f"data: {metadata_json}\n\n"
                
                # Stream cleaned content using sync generator (consistent with clean_markdown_content_stream)
                generator = document_service.vllm_service.clean_markdown_content_stream(raw_markdown)
                for token in generator:  # Use sync iteration like in the working endpoint
                    # Ensure token is properly encoded as UTF-8 string
                    if isinstance(token, bytes):
                        token = token.decode('utf-8', errors='replace')
                    yield token
                    
            except Exception as stream_error:
                logger.error(f"Error in PDF stream generation: {stream_error}")
                error_msg = f"\n\n[ERROR: {str(stream_error)}]"
                yield error_msg
                raise
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain; charset=utf-8",  # Explicitly set UTF-8 charset
            headers={
                "X-Content-Type": "streaming",
                "X-Filename": encode_filename_for_header(file.filename),  # Properly encode filename
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing file for streaming: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    logger.info(f"vLLM service URL: {settings.vllm_base_url}")
    logger.info(f"vLLM model: {settings.vllm_model_name}")
    logger.info(f"vLLM auto-start: {settings.vllm_auto_start}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    ) 