"""
Tests for health check and status endpoints
"""

import pytest
import httpx


@pytest.mark.asyncio
async def test_health_check(client: httpx.AsyncClient):
    """Test the basic health check endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "api" in data
    assert "vllm" in data
    assert data["api"] == "healthy"
    
    # Response time should be reasonable
    assert response.elapsed.total_seconds() < 5.0


@pytest.mark.asyncio
async def test_vllm_status(client: httpx.AsyncClient):
    """Test the vLLM status endpoint."""
    response = await client.get("/vllm/status")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "process_running" in data
    assert "gpu_available" in data
    assert "model" in data
    
    # Validate data types
    assert isinstance(data["process_running"], bool)
    assert isinstance(data["gpu_available"], bool)
    assert isinstance(data["model"], str)


@pytest.mark.asyncio
async def test_health_check_response_time(client: httpx.AsyncClient):
    """Test that health check responds quickly."""
    import time
    
    start_time = time.time()
    response = await client.get("/health")
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 2.0  # Should respond within 2 seconds 