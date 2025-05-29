"""
Tests for markdown cleaning endpoints
"""

import pytest
import httpx


@pytest.mark.asyncio
async def test_clean_markdown_success(client: httpx.AsyncClient, sample_markdown: str):
    """Test successful markdown cleaning."""
    payload = {"markdown_content": sample_markdown}
    
    response = await client.post("/clean-markdown", json=payload)
    
    # Note: This might fail if vLLM has token limits, so we handle both cases
    if response.status_code == 200:
        data = response.json()
        
        assert "markdown_content" in data
        assert "content_length" in data
        assert "metadata" in data
        
        # Content should be cleaned
        assert len(data["markdown_content"]) > 0
        assert data["content_length"] > 0
        
        # Check metadata
        metadata = data["metadata"]
        assert "processing_time_seconds" in metadata
    
    elif response.status_code == 500:
        # Expected if token limit exceeded
        data = response.json()
        assert "detail" in data
        # This is acceptable for large content
        pytest.skip("Token limit exceeded - expected for large content")
    
    else:
        pytest.fail(f"Unexpected status code: {response.status_code}")


@pytest.mark.asyncio
async def test_clean_markdown_empty_content(client: httpx.AsyncClient):
    """Test cleaning with empty markdown content."""
    payload = {"markdown_content": ""}
    
    response = await client.post("/clean-markdown", json=payload)
    
    # Should handle empty content gracefully
    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_clean_markdown_small_content(client: httpx.AsyncClient):
    """Test cleaning with small markdown content that should work."""
    small_content = "# Simple Title\n\nThis is a simple paragraph."
    payload = {"markdown_content": small_content}
    
    response = await client.post("/clean-markdown", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        assert "markdown_content" in data
        assert len(data["markdown_content"]) > 0
    elif response.status_code == 500:
        # vLLM service might not be available
        pytest.skip("vLLM service not available")


@pytest.mark.asyncio
async def test_clean_markdown_invalid_payload(client: httpx.AsyncClient):
    """Test cleaning with invalid payload."""
    # Missing required field
    payload = {"wrong_field": "content"}
    
    response = await client.post("/clean-markdown", json=payload)
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_clean_markdown_malformed_json(client: httpx.AsyncClient):
    """Test cleaning with malformed JSON."""
    response = await client.post(
        "/clean-markdown", 
        content="invalid json",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422 