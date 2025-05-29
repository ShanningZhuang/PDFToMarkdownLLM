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
    
    # Check response format based on API docs
    assert "success" in data
    assert "message" in data
    
    if response.status_code == 200:
        # Successful start should include status
        assert "status" in data
        assert isinstance(data["success"], bool)
        
        # Check status structure
        status = data["status"]
        required_status_fields = ["process_running", "gpu_available", "model"]
        for field in required_status_fields:
            assert field in status


@pytest.mark.asyncio
async def test_vllm_stop(client: httpx.AsyncClient):
    """Test stopping vLLM service."""
    response = await client.post("/vllm/stop")
    
    # Should either succeed or indicate not running
    assert response.status_code in [200, 400]
    
    data = response.json()
    
    # Check response format
    assert "success" in data
    assert "message" in data
    assert isinstance(data["success"], bool)


@pytest.mark.asyncio
async def test_vllm_restart(client: httpx.AsyncClient):
    """Test restarting vLLM service."""
    response = await client.post("/vllm/restart")
    
    # Restart should work regardless of current state
    assert response.status_code == 200
    
    data = response.json()
    
    # Check response format
    assert "success" in data
    assert "message" in data
    assert "status" in data
    assert isinstance(data["success"], bool)
    
    # Check status structure
    status = data["status"]
    required_status_fields = ["process_running", "gpu_available", "model"]
    for field in required_status_fields:
        assert field in status


@pytest.mark.asyncio
async def test_vllm_start_with_model(client: httpx.AsyncClient):
    """Test starting vLLM service with specific model."""
    model_name = "mistralai/Mistral-7B-Instruct-v0.3"
    request_body = {"model_name": model_name}
    
    response = await client.post("/vllm/start", json=request_body)
    
    assert response.status_code in [200, 400]
    data = response.json()
    
    assert "success" in data
    assert "message" in data
    
    if response.status_code == 200 and data["success"]:
        assert "status" in data
        status = data["status"]
        # The model in status should match what we requested (if it started successfully)
        if status.get("process_running"):
            assert status["model"] == model_name


@pytest.mark.asyncio
async def test_vllm_restart_with_model(client: httpx.AsyncClient):
    """Test restarting vLLM service with specific model."""
    model_name = "mistralai/Mistral-7B-Instruct-v0.3"
    request_body = {"model_name": model_name}
    
    response = await client.post("/vllm/restart", json=request_body)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "success" in data
    assert "message" in data
    assert "status" in data


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
    required_fields = ["process_running", "gpu_available", "model"]
    for field in required_fields:
        assert field in final_status


@pytest.mark.asyncio
async def test_vllm_management_response_format(client: httpx.AsyncClient):
    """Test that all vLLM management endpoints return proper format."""
    
    # Test start endpoint response format
    start_response = await client.post("/vllm/start")
    assert start_response.status_code in [200, 400]
    start_data = start_response.json()
    
    required_start_fields = ["success", "message"]
    for field in required_start_fields:
        assert field in start_data
    
    # Test stop endpoint response format
    stop_response = await client.post("/vllm/stop")
    assert stop_response.status_code in [200, 400]
    stop_data = stop_response.json()
    
    required_stop_fields = ["success", "message"]
    for field in required_stop_fields:
        assert field in stop_data
    
    # Test restart endpoint response format
    restart_response = await client.post("/vllm/restart")
    assert restart_response.status_code == 200
    restart_data = restart_response.json()
    
    required_restart_fields = ["success", "message", "status"]
    for field in required_restart_fields:
        assert field in restart_data


@pytest.mark.asyncio
async def test_vllm_status_consistency(client: httpx.AsyncClient):
    """Test that vLLM status is consistent across endpoints."""
    # Get status from status endpoint
    status_response = await client.get("/vllm/status")
    assert status_response.status_code == 200
    status_data = status_response.json()
    
    # Get status from health endpoint
    health_response = await client.get("/health")
    assert health_response.status_code == 200
    health_data = health_response.json()
    
    # If health contains vllm_process, key fields should match
    if "vllm_process" in health_data:
        vllm_process = health_data["vllm_process"]
        
        # Key fields should be consistent
        consistency_fields = ["process_running", "gpu_available", "model"]
        for field in consistency_fields:
            if field in vllm_process and field in status_data:
                assert vllm_process[field] == status_data[field], f"Inconsistent {field}: health={vllm_process[field]}, status={status_data[field]}"


@pytest.mark.asyncio
async def test_vllm_management_error_handling(client: httpx.AsyncClient):
    """Test error handling in vLLM management."""
    # Test invalid endpoints
    response = await client.post("/vllm/invalid")
    assert response.status_code == 404
    
    # Test invalid methods
    response = await client.get("/vllm/start")
    assert response.status_code == 405  # Method not allowed


@pytest.mark.asyncio
async def test_vllm_service_lifecycle(client: httpx.AsyncClient):
    """Test complete vLLM service lifecycle."""
    
    # 1. Check initial status
    status_response = await client.get("/vllm/status")
    assert status_response.status_code == 200
    initial_status = status_response.json()
    
    print(f"\n📊 vLLM Service Lifecycle Test:")
    print(f"Initial state - Running: {initial_status.get('process_running', 'unknown')}")
    
    # 2. Try to start service
    start_response = await client.post("/vllm/start")
    start_data = start_response.json()
    print(f"Start attempt - Success: {start_data.get('success', 'unknown')}, Message: {start_data.get('message', 'none')}")
    
    # 3. Wait and check status
    await asyncio.sleep(1)
    status_response = await client.get("/vllm/status")
    after_start_status = status_response.json()
    print(f"After start - Running: {after_start_status.get('process_running', 'unknown')}")
    
    # 4. Try restart
    restart_response = await client.post("/vllm/restart")
    restart_data = restart_response.json()
    print(f"Restart attempt - Success: {restart_data.get('success', 'unknown')}")
    
    # 5. Final status check
    await asyncio.sleep(1)
    status_response = await client.get("/vllm/status")
    final_status = status_response.json()
    print(f"Final state - Running: {final_status.get('process_running', 'unknown')}")
    
    # All operations should return valid responses
    assert start_response.status_code in [200, 400]
    assert restart_response.status_code == 200
    
    # All responses should have required fields
    assert "success" in start_data
    assert "message" in start_data
    assert "success" in restart_data
    assert "message" in restart_data 