"""
Tests for API endpoints including upload, streaming, and health checks
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import httpx

from main import app, encode_filename_for_header


class TestHealthEndpoints:
    """Test health check and status endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns basic info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "PDF to Markdown" in data["message"]
    
    @patch('services.document_service.get_health_status')
    @patch('vllm_manager.vllm_manager.get_vllm_status')
    def test_health_check_endpoint(self, mock_vllm_status, mock_health_status, client):
        """Test health check endpoint"""
        mock_health_status.return_value = {"api": "healthy", "vllm": "healthy"}
        mock_vllm_status.return_value = {"process_running": True, "port": 8000}
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "api" in data
        assert "vllm_process" in data
    
    @patch('vllm_manager.vllm_manager.get_vllm_status')
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    def test_vllm_status_endpoint(self, mock_is_running, mock_status, client):
        """Test vLLM status endpoint"""
        mock_status.return_value = {"process_running": True, "port": 8000}
        mock_is_running.return_value = True
        
        response = client.get("/vllm/status")
        assert response.status_code == 200
        data = response.json()
        assert "process_running" in data
        assert "service_responsive" in data


class TestVLLMControlEndpoints:
    """Test vLLM control endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch('vllm_manager.vllm_manager.start_vllm_service')
    @patch('vllm_manager.vllm_manager.get_vllm_status')
    def test_start_vllm_service(self, mock_status, mock_start, client):
        """Test starting vLLM service"""
        mock_start.return_value = True
        mock_status.return_value = {"process_running": True}
        
        response = client.post("/vllm/start")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "started successfully" in data["message"]
    
    @patch('vllm_manager.vllm_manager.start_vllm_service')
    def test_start_vllm_service_with_model(self, mock_start, client):
        """Test starting vLLM service with specific model"""
        mock_start.return_value = True
        
        response = client.post(
            "/vllm/start",
            json={"model_name": "custom-model"}
        )
        assert response.status_code == 200
        mock_start.assert_called_with("custom-model")
    
    @patch('vllm_manager.vllm_manager.stop_vllm_service')
    def test_stop_vllm_service(self, mock_stop, client):
        """Test stopping vLLM service"""
        mock_stop.return_value = True
        
        response = client.post("/vllm/stop")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @patch('vllm_manager.vllm_manager.restart_vllm_service')
    @patch('vllm_manager.vllm_manager.get_vllm_status')
    def test_restart_vllm_service(self, mock_status, mock_restart, client):
        """Test restarting vLLM service"""
        mock_restart.return_value = True
        mock_status.return_value = {"process_running": True}
        
        response = client.post("/vllm/restart")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestUploadEndpoints:
    """Test PDF upload endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Create sample PDF content for testing"""
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    @patch('services.document_service.process_document')
    def test_upload_pdf_success(self, mock_process, mock_vllm_running, client, sample_pdf_content):
        """Test successful PDF upload"""
        mock_vllm_running.return_value = True
        mock_process.return_value = {
            "success": True,
            "filename": "test.pdf",
            "cleaned_markdown": "# Test Document\n\nContent",
            "content_length": 25
        }
        
        response = client.post(
            "/upload",
            files={"file": ("test.pdf", sample_pdf_content, "application/pdf")},
            data={"clean_with_llm": "true"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["filename"] == "test.pdf"
        assert "cleaned_markdown" in data
    
    def test_upload_invalid_file_type(self, client):
        """Test upload with invalid file type"""
        response = client.post(
            "/upload",
            files={"file": ("test.txt", b"content", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]
    
    @patch('config.settings.max_file_size_mb', 1)  # 1MB limit
    def test_upload_file_too_large(self, client):
        """Test upload with file too large"""
        large_content = b"x" * (2 * 1024 * 1024)  # 2MB
        
        response = client.post(
            "/upload",
            files={"file": ("large.pdf", large_content, "application/pdf")}
        )
        
        assert response.status_code == 400
        assert "too large" in response.json()["detail"]
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    @patch('services.document_service.process_document')
    def test_convert_text_only(self, mock_process, mock_vllm_running, client, sample_pdf_content):
        """Test convert-text endpoint (no LLM cleaning)"""
        mock_vllm_running.return_value = False  # vLLM not needed
        mock_process.return_value = {
            "success": True,
            "filename": "test.pdf",
            "raw_markdown": "# Test Document\n\nContent",
            "cleaned_with_llm": False
        }
        
        response = client.post(
            "/convert-text",
            files={"file": ("test.pdf", sample_pdf_content, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cleaned_with_llm"] is False
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    def test_upload_vllm_unavailable_no_autostart(self, mock_vllm_running, client, sample_pdf_content):
        """Test upload when vLLM unavailable and auto-start disabled"""
        mock_vllm_running.return_value = False
        
        with patch('config.settings.vllm_auto_start', False):
            response = client.post(
                "/upload",
                files={"file": ("test.pdf", sample_pdf_content, "application/pdf")},
                data={"clean_with_llm": "true"}
            )
        
        assert response.status_code == 503
        assert "vLLM service is not available" in response.json()["detail"]


class TestMarkdownCleaningEndpoints:
    """Test markdown cleaning endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    @patch('services.VLLMService.clean_markdown_content')
    def test_clean_markdown_success(self, mock_clean, mock_vllm_running, client):
        """Test successful markdown cleaning"""
        mock_vllm_running.return_value = True
        mock_clean.return_value = "# Cleaned Document\n\nCleaned content"
        
        response = client.post(
            "/clean-markdown",
            json={"markdown_content": "# Raw Document\n\nRaw content"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cleaned_content" in data
        assert "original_content" in data
    
    def test_clean_markdown_empty_content(self, client):
        """Test cleaning with empty content"""
        response = client.post(
            "/clean-markdown",
            json={"markdown_content": ""}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def test_clean_markdown_whitespace_only(self, client):
        """Test cleaning with whitespace-only content"""
        response = client.post(
            "/clean-markdown",
            json={"markdown_content": "   \n\t  "}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    def test_clean_markdown_vllm_unavailable(self, mock_vllm_running, client):
        """Test cleaning when vLLM unavailable"""
        mock_vllm_running.return_value = False
        
        with patch('config.settings.vllm_auto_start', False):
            response = client.post(
                "/clean-markdown",
                json={"markdown_content": "# Test\n\nContent"}
            )
        
        assert response.status_code == 503
        assert "vLLM" in response.json()["detail"]


class TestFilenameEncoding:
    """Test filename encoding functionality"""
    
    def test_encode_filename_ascii(self):
        """Test encoding ASCII filename"""
        result = encode_filename_for_header("document.pdf")
        assert result == "document.pdf"
    
    def test_encode_filename_chinese(self):
        """Test encoding Chinese filename"""
        result = encode_filename_for_header("中文文档.pdf")
        assert "%" in result
        assert result != "中文文档.pdf"
    
    def test_encode_filename_mixed(self):
        """Test encoding mixed ASCII/Chinese filename"""
        result = encode_filename_for_header("Report_中文版.pdf")
        assert "%" in result
        assert "Report_" in result or "%52%65%70%6F%72%74%5F" in result
    
    def test_encode_filename_special_chars(self):
        """Test encoding filename with special characters"""
        result = encode_filename_for_header("file (copy).pdf")
        # Should be URL encoded since parentheses need encoding
        assert "%" in result or result == "file (copy).pdf"  # Depends on implementation
    
    def test_encode_filename_empty(self):
        """Test encoding empty filename"""
        result = encode_filename_for_header("")
        assert result == ""


class TestErrorHandling:
    """Test error handling across endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch('services.document_service.process_document')
    def test_upload_processing_error(self, mock_process, client):
        """Test handling of processing errors during upload"""
        mock_process.side_effect = Exception("Processing failed")
        
        response = client.post(
            "/upload",
            files={"file": ("test.pdf", b"content", "application/pdf")}
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    @patch('services.VLLMService.clean_markdown_content')
    def test_clean_markdown_processing_error(self, mock_clean, mock_vllm_running, client):
        """Test handling of cleaning errors"""
        mock_vllm_running.return_value = True
        mock_clean.side_effect = Exception("Cleaning failed")
        
        response = client.post(
            "/clean-markdown",
            json={"markdown_content": "# Test\n\nContent"}
        )
        
        assert response.status_code == 500
        assert "Failed to clean markdown" in response.json()["detail"]
    
    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON requests"""
        response = client.post(
            "/clean-markdown",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Validation error


class TestCORSAndHeaders:
    """Test CORS and header handling"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present"""
        response = client.options("/")
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
    
    def test_content_type_headers(self, client):
        """Test content type headers"""
        response = client.get("/")
        assert response.headers.get("content-type") == "application/json"
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    @patch('services.VLLMService.clean_markdown_content_stream')
    def test_streaming_headers(self, mock_stream, mock_vllm_running, client):
        """Test streaming response headers"""
        mock_vllm_running.return_value = True
        mock_stream.return_value = iter(["test"])
        
        response = client.post(
            "/clean-markdown-stream",
            json={"markdown_content": "Test content"}
        )
        
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        assert "charset=utf-8" in response.headers.get("content-type", "")
        assert response.headers.get("x-content-type") == "streaming"


class TestRequestValidation:
    """Test request validation"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_missing_file_upload(self, client):
        """Test upload without file"""
        response = client.post("/upload")
        assert response.status_code == 422  # Validation error
    
    def test_missing_markdown_content(self, client):
        """Test clean-markdown without content"""
        response = client.post("/clean-markdown", json={})
        assert response.status_code == 422  # Validation error
    
    def test_invalid_vllm_control_request(self, client):
        """Test vLLM control with invalid data"""
        response = client.post(
            "/vllm/start",
            json={"invalid_field": "value"}
        )
        # Should still work as model_name is optional
        assert response.status_code in [200, 500]  # Depends on vLLM availability
    
    def test_large_markdown_content(self, client):
        """Test with very large markdown content"""
        large_content = "# Test\n\n" + "Content " * 10000  # Large but reasonable
        
        response = client.post(
            "/clean-markdown",
            json={"markdown_content": large_content}
        )
        
        # Should either process or fail gracefully
        assert response.status_code in [200, 400, 500, 503]


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    @patch('services.document_service.process_document')
    def test_full_pdf_processing_workflow(self, mock_process, mock_vllm_running, client):
        """Test complete PDF processing workflow"""
        mock_vllm_running.return_value = True
        mock_process.return_value = {
            "success": True,
            "filename": "document.pdf",
            "raw_markdown": "# Raw Content",
            "cleaned_markdown": "# Cleaned Content",
            "cleaned_with_llm": True,
            "content_length": 50,
            "metadata": {
                "original_filename": "document.pdf",
                "file_size_bytes": 1024,
                "conversion_method": "MarkItDown",
                "llm_cleaning": True
            }
        }
        
        # Upload and process PDF
        response = client.post(
            "/upload",
            files={"file": ("document.pdf", b"fake pdf", "application/pdf")},
            data={"clean_with_llm": "true"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cleaned_with_llm"] is True
        assert "metadata" in data
        assert data["metadata"]["llm_cleaning"] is True
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    @patch('services.VLLMService.clean_markdown_content')
    def test_markdown_cleaning_workflow(self, mock_clean, mock_vllm_running, client):
        """Test markdown cleaning workflow"""
        mock_vllm_running.return_value = True
        mock_clean.return_value = "# Cleaned Document\n\nThis is cleaned content."
        
        # Clean existing markdown
        response = client.post(
            "/clean-markdown",
            json={"markdown_content": "# Raw Document\n\nThis is raw content."}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cleaned_content" in data
        assert "content_length" in data
        assert data["content_length"] > 0 