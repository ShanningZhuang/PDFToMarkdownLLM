"""
Tests for vLLM management endpoints
"""

import pytest
import httpx
import asyncio


@pytest.mark.asyncio
async def test_vllm_start(client: httpx.AsyncClient):
    """Test starting vLLM service."""
    response = await client.post("/vllm/start")
    
    # Should either succeed or indicate already running
    assert response.status_code in [200, 400]
    
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_vllm_stop(client: httpx.AsyncClient):
    """Test stopping vLLM service."""
    response = await client.post("/vllm/stop")
    
    # Should either succeed or indicate not running
    assert response.status_code in [200, 400]
    
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_vllm_restart(client: httpx.AsyncClient):
    """Test restarting vLLM service."""
    response = await client.post("/vllm/restart")
    
    # Restart should work regardless of current state
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_vllm_status_after_operations(client: httpx.AsyncClient):
    """Test vLLM status after management operations."""
    # Get initial status
    status_response = await client.get("/vllm/status")
    assert status_response.status_code == 200
    
    initial_status = status_response.json()
    
    # Try to start service
    start_response = await client.post("/vllm/start")
    assert start_response.status_code in [200, 400]
    
    # Wait a moment for service to potentially start
    await asyncio.sleep(2)
    
    # Check status again
    status_response = await client.get("/vllm/status")
    assert status_response.status_code == 200
    
    final_status = status_response.json()
    
    # Status should have consistent structure
    assert "process_running" in final_status
    assert "gpu_available" in final_status
    assert "model" in final_status


@pytest.mark.asyncio
async def test_vllm_management_error_handling(client: httpx.AsyncClient):
    """Test error handling in vLLM management."""
    # Test invalid endpoints
    response = await client.post("/vllm/invalid")
    assert response.status_code == 404
    
    # Test invalid methods
    response = await client.get("/vllm/start")
    assert response.status_code == 405  # Method not allowed 