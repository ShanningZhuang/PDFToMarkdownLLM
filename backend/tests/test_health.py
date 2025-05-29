"""
Tests for health check and status endpoints
"""

import pytest
import httpx


@pytest.mark.asyncio
async def test_root_endpoint(client: httpx.AsyncClient):
    """Test the root endpoint."""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert data["message"] == "PDF to Markdown Converter API is running"


@pytest.mark.asyncio
async def test_health_check(client: httpx.AsyncClient):
    """Test the basic health check endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check basic health fields
    assert "api" in data
    assert "vllm" in data
    assert data["api"] == "healthy"
    
    # Check that vllm status is a valid value
    assert data["vllm"] in ["healthy", "unhealthy"] or data["vllm"].startswith("error:")
    
    # Check for vllm_process details
    if "vllm_process" in data:
        vllm_process = data["vllm_process"]
        expected_fields = ["process_running", "gpu_available", "model"]
        for field in expected_fields:
            assert field in vllm_process
    
    # Response time should be reasonable
    assert response.elapsed.total_seconds() < 5.0


@pytest.mark.asyncio
async def test_vllm_status(client: httpx.AsyncClient):
    """Test the vLLM status endpoint."""
    response = await client.get("/vllm/status")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields based on API docs
    required_fields = ["process_running", "gpu_available", "model"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Validate data types
    assert isinstance(data["process_running"], bool)
    assert isinstance(data["gpu_available"], bool)
    assert isinstance(data["model"], str)
    
    # Check optional fields
    if data["process_running"]:
        # If process is running, we might have additional fields
        optional_fields = ["process_pid", "port", "memory_usage_mb"]
        for field in optional_fields:
            if field in data:
                if field == "process_pid":
                    assert isinstance(data[field], (int, type(None)))
                elif field == "port":
                    assert isinstance(data[field], int)
                    assert 1000 <= data[field] <= 65535
                elif field == "memory_usage_mb":
                    assert isinstance(data[field], (int, float))
                    assert data[field] >= 0


@pytest.mark.asyncio
async def test_health_check_response_time(client: httpx.AsyncClient):
    """Test that health check responds quickly."""
    import time
    
    start_time = time.time()
    response = await client.get("/health")
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 2.0  # Should respond within 2 seconds


@pytest.mark.asyncio
async def test_health_endpoints_consistency(client: httpx.AsyncClient):
    """Test that health endpoints return consistent information."""
    # Get health check response
    health_response = await client.get("/health")
    assert health_response.status_code == 200
    health_data = health_response.json()
    
    # Get vLLM status response
    status_response = await client.get("/vllm/status")
    assert status_response.status_code == 200
    status_data = status_response.json()
    
    # The vLLM process info in health should be consistent with status
    if "vllm_process" in health_data:
        vllm_process = health_data["vllm_process"]
        
        # Key fields should match
        assert vllm_process["process_running"] == status_data["process_running"]
        assert vllm_process["gpu_available"] == status_data["gpu_available"]
        assert vllm_process["model"] == status_data["model"]


@pytest.mark.asyncio
async def test_health_check_detailed_format(client: httpx.AsyncClient):
    """Test the detailed health check response format."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Basic structure validation
    assert isinstance(data, dict)
    assert len(data) >= 2  # At least api and vllm fields
    
    # API status should always be healthy if we get 200
    assert data["api"] == "healthy"
    
    # vLLM status validation
    vllm_status = data["vllm"]
    valid_vllm_statuses = ["healthy", "unhealthy"]
    assert vllm_status in valid_vllm_statuses or vllm_status.startswith("error:")
    
    # If vllm_process is present, validate its structure
    if "vllm_process" in data:
        vllm_process = data["vllm_process"]
        assert isinstance(vllm_process, dict)
        
        # Required fields in vllm_process
        required_process_fields = ["process_running", "gpu_available", "model"]
        for field in required_process_fields:
            assert field in vllm_process 