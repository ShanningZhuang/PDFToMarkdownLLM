"""
Tests for PDF conversion endpoints
"""

import pytest
import httpx
from pathlib import Path


@pytest.mark.asyncio
async def test_pdf_upload_with_llm(client: httpx.AsyncClient, sample_pdf_path: str):
    """Test PDF upload with LLM cleaning enabled."""
    pdf_file = Path(sample_pdf_path)
    
    with open(pdf_file, 'rb') as f:
        files = {'file': (pdf_file.name, f, 'application/pdf')}
        params = {'clean_with_llm': True}
        
        response = await client.post("/upload", files=files, params=params)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "markdown_content" in data
    assert "content_length" in data
    assert "cleaned_with_llm" in data
    assert "metadata" in data
    
    # Validate content
    assert len(data["markdown_content"]) > 0
    assert data["content_length"] > 0
    assert data["cleaned_with_llm"] is True
    
    # Check metadata
    metadata = data["metadata"]
    assert "conversion_method" in metadata
    assert "processing_time_seconds" in metadata


@pytest.mark.asyncio
async def test_pdf_upload_without_llm(client: httpx.AsyncClient, sample_pdf_path: str):
    """Test PDF upload without LLM cleaning."""
    pdf_file = Path(sample_pdf_path)
    
    with open(pdf_file, 'rb') as f:
        files = {'file': (pdf_file.name, f, 'application/pdf')}
        params = {'clean_with_llm': False}
        
        response = await client.post("/upload", files=files, params=params)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "markdown_content" in data
    assert "content_length" in data
    assert "cleaned_with_llm" in data
    assert data["cleaned_with_llm"] is False


@pytest.mark.asyncio
async def test_convert_text_only(client: httpx.AsyncClient, sample_pdf_path: str):
    """Test text-only conversion endpoint."""
    pdf_file = Path(sample_pdf_path)
    
    with open(pdf_file, 'rb') as f:
        files = {'file': (pdf_file.name, f, 'application/pdf')}
        
        response = await client.post("/convert-text", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "markdown_content" in data
    assert "content_length" in data
    assert len(data["markdown_content"]) > 0


@pytest.mark.asyncio
async def test_invalid_file_upload(client: httpx.AsyncClient):
    """Test upload with invalid file type."""
    # Create a fake text file
    fake_content = b"This is not a PDF file"
    files = {'file': ('test.txt', fake_content, 'text/plain')}
    
    response = await client.post("/upload", files=files)
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_missing_file_upload(client: httpx.AsyncClient):
    """Test upload without file."""
    response = await client.post("/upload")
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_large_pdf_handling(client: httpx.AsyncClient, sample_pdf_path: str):
    """Test handling of PDF files and response time."""
    pdf_file = Path(sample_pdf_path)
    file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
    
    import time
    start_time = time.time()
    
    with open(pdf_file, 'rb') as f:
        files = {'file': (pdf_file.name, f, 'application/pdf')}
        params = {'clean_with_llm': False}  # Faster without LLM
        
        response = await client.post("/upload", files=files, params=params)
    
    processing_time = time.time() - start_time
    
    assert response.status_code == 200
    
    # Performance expectations (adjust based on your requirements)
    if file_size_mb < 1:
        assert processing_time < 10  # Small files should process quickly
    elif file_size_mb < 5:
        assert processing_time < 30  # Medium files
    # Larger files may take longer 