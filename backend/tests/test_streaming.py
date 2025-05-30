"""
Tests for streaming functionality including token-by-token streaming
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi.responses import StreamingResponse
import httpx

from main import app
from services import VLLMService, DocumentProcessingService


class TestStreamingGenerators:
    """Test streaming generator behavior"""
    
    def test_sync_generator_immediate_yield(self):
        """Sync generators should yield immediately"""
        def sync_gen():
            yield "chunk1"
            yield "chunk2"
            yield "chunk3"
        
        chunks = []
        start_time = time.time()
        
        for chunk in sync_gen():
            chunks.append((chunk, time.time() - start_time))
        
        assert len(chunks) == 3
        assert chunks[0][0] == "chunk1"
        # All chunks should be yielded almost immediately
        assert all(timing < 0.1 for _, timing in chunks)
    
    def test_async_generator_collection(self):
        """Async generators get collected before yielding"""
        async def async_gen():
            yield "chunk1"
            await asyncio.sleep(0.1)
            yield "chunk2"
            await asyncio.sleep(0.1)
            yield "chunk3"
        
        async def collect_async():
            chunks = []
            start_time = time.time()
            
            # Simulate FastAPI's behavior with async generators
            collected = []
            async for chunk in async_gen():
                collected.append(chunk)
            
            # All chunks collected, now "send" them
            for chunk in collected:
                chunks.append((chunk, time.time() - start_time))
            
            return chunks
        
        chunks = asyncio.run(collect_async())
        assert len(chunks) == 3
        # All chunks should have similar timestamps (buffered)
        timestamps = [timing for _, timing in chunks]
        assert max(timestamps) - min(timestamps) < 0.05


class TestVLLMStreamingService:
    """Test vLLM streaming service functionality"""
    
    @pytest.fixture
    def vllm_service(self):
        return VLLMService()
    
    @patch('services.VLLMService.client')
    def test_clean_markdown_content_stream_generator_type(self, mock_client, vllm_service):
        """Test that clean_markdown_content_stream returns sync generator"""
        # Mock the OpenAI client response
        mock_stream = Mock()
        mock_stream.__iter__ = Mock(return_value=iter([
            Mock(choices=[Mock(delta=Mock(content="Hello"), finish_reason=None)]),
            Mock(choices=[Mock(delta=Mock(content=" World"), finish_reason=None)]),
            Mock(choices=[Mock(delta=Mock(content=None), finish_reason="stop")])
        ]))
        mock_client.chat.completions.create.return_value = mock_stream
        
        # Get the generator
        generator = vllm_service.clean_markdown_content_stream("Test content")
        
        # Should be a regular generator, not async
        import inspect
        assert inspect.isgenerator(generator)
        assert not inspect.isasyncgen(generator)
    
    @patch('services.VLLMService.client')
    def test_clean_markdown_content_stream_yields_tokens(self, mock_client, vllm_service):
        """Test that streaming yields individual tokens"""
        # Mock the OpenAI client response
        mock_chunks = [
            Mock(choices=[Mock(delta=Mock(content="Hello"), finish_reason=None)]),
            Mock(choices=[Mock(delta=Mock(content=" "), finish_reason=None)]),
            Mock(choices=[Mock(delta=Mock(content="World"), finish_reason=None)]),
            Mock(choices=[Mock(delta=Mock(content=None), finish_reason="stop")])
        ]
        mock_stream = Mock()
        mock_stream.__iter__ = Mock(return_value=iter(mock_chunks))
        mock_client.chat.completions.create.return_value = mock_stream
        
        # Collect tokens
        tokens = list(vllm_service.clean_markdown_content_stream("Test content"))
        
        assert len(tokens) == 3
        assert tokens == ["Hello", " ", "World"]
    
    @patch('services.VLLMService.client')
    def test_clean_markdown_content_stream_thinking_filter(self, mock_client, vllm_service):
        """Test that thinking tags are filtered out"""
        # Mock response with thinking tags
        mock_chunks = [
            Mock(choices=[Mock(delta=Mock(content="<think>"), finish_reason=None)]),
            Mock(choices=[Mock(delta=Mock(content="This is thinking"), finish_reason=None)]),
            Mock(choices=[Mock(delta=Mock(content="</think>"), finish_reason=None)]),
            Mock(choices=[Mock(delta=Mock(content="Real content"), finish_reason=None)]),
            Mock(choices=[Mock(delta=Mock(content=None), finish_reason="stop")])
        ]
        mock_stream = Mock()
        mock_stream.__iter__ = Mock(return_value=iter(mock_chunks))
        mock_client.chat.completions.create.return_value = mock_stream
        
        # Collect tokens
        tokens = list(vllm_service.clean_markdown_content_stream("Test content"))
        
        # Should only get real content, thinking should be filtered
        assert "Real content" in tokens
        assert not any("<think>" in token for token in tokens)
        assert not any("</think>" in token for token in tokens)
        assert not any("This is thinking" in token for token in tokens)
    
    @patch('services.VLLMService.client')
    def test_clean_markdown_content_stream_encoding_safety(self, mock_client, vllm_service):
        """Test that streaming handles encoding properly"""
        # Mock response with Chinese content
        mock_chunks = [
            Mock(choices=[Mock(delta=Mock(content="中文"), finish_reason=None)]),
            Mock(choices=[Mock(delta=Mock(content="测试"), finish_reason=None)]),
            Mock(choices=[Mock(delta=Mock(content=None), finish_reason="stop")])
        ]
        mock_stream = Mock()
        mock_stream.__iter__ = Mock(return_value=iter(mock_chunks))
        mock_client.chat.completions.create.return_value = mock_stream
        
        # Collect tokens
        tokens = list(vllm_service.clean_markdown_content_stream("Test content"))
        
        # All tokens should be UTF-8 encodable
        for token in tokens:
            token.encode('utf-8')  # Should not raise
            assert isinstance(token, str)


class TestStreamingEndpoints:
    """Test streaming API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    @patch('services.VLLMService.clean_markdown_content_stream')
    def test_clean_markdown_stream_endpoint(self, mock_stream, mock_vllm_running, client):
        """Test /clean-markdown-stream endpoint"""
        mock_vllm_running.return_value = True
        mock_stream.return_value = iter(["Hello", " ", "World", "!"])
        
        response = client.post(
            "/clean-markdown-stream",
            json={"markdown_content": "Test content"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "streaming" in response.headers.get("x-content-type", "")
        
        # Content should be streamed
        content = response.text
        assert "Hello World!" in content
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    @patch('services.PDFConverterService.convert_pdf_to_markdown')
    @patch('services.VLLMService.clean_markdown_content_stream')
    def test_upload_stream_endpoint(self, mock_stream, mock_convert, mock_vllm_running, client):
        """Test /upload-stream endpoint"""
        mock_vllm_running.return_value = True
        mock_convert.return_value = "# Test Document\n\nContent"
        mock_stream.return_value = iter(["Cleaned", " ", "content"])
        
        # Create a fake PDF file
        pdf_content = b"fake pdf content"
        
        response = client.post(
            "/upload-stream",
            files={"file": ("test.pdf", pdf_content, "application/pdf")}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "streaming" in response.headers.get("x-content-type", "")
        
        # Should include metadata and content
        content = response.text
        assert "data:" in content  # Metadata
        assert "Cleaned content" in content
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    @patch('services.PDFConverterService.convert_pdf_to_markdown')
    @patch('services.VLLMService.clean_markdown_content_stream')
    def test_upload_stream_chinese_filename(self, mock_stream, mock_convert, mock_vllm_running, client):
        """Test /upload-stream with Chinese filename"""
        mock_vllm_running.return_value = True
        mock_convert.return_value = "# 中文文档\n\n内容"
        mock_stream.return_value = iter(["中文", "内容"])
        
        # Create a fake PDF file with Chinese filename
        pdf_content = b"fake pdf content"
        chinese_filename = "中文文档.pdf"
        
        response = client.post(
            "/upload-stream",
            files={"file": (chinese_filename, pdf_content, "application/pdf")}
        )
        
        assert response.status_code == 200
        
        # Filename should be URL encoded in header
        x_filename = response.headers.get("x-filename", "")
        assert "%" in x_filename  # Should be URL encoded
        assert chinese_filename not in x_filename  # Original should not be there
    
    def test_clean_markdown_stream_empty_content(self, client):
        """Test streaming with empty content"""
        response = client.post(
            "/clean-markdown-stream",
            json={"markdown_content": ""}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def test_upload_stream_invalid_file_type(self, client):
        """Test streaming with invalid file type"""
        response = client.post(
            "/upload-stream",
            files={"file": ("test.txt", b"content", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]


class TestStreamingPerformance:
    """Test streaming performance characteristics"""
    
    @patch('services.VLLMService.client')
    def test_streaming_latency(self, mock_client):
        """Test that streaming has low latency"""
        vllm_service = VLLMService()
        
        # Mock delayed response
        def delayed_chunks():
            yield Mock(choices=[Mock(delta=Mock(content="First"), finish_reason=None)])
            time.sleep(0.1)
            yield Mock(choices=[Mock(delta=Mock(content="Second"), finish_reason=None)])
            time.sleep(0.1)
            yield Mock(choices=[Mock(delta=Mock(content=None), finish_reason="stop")])
        
        mock_stream = Mock()
        mock_stream.__iter__ = Mock(return_value=delayed_chunks())
        mock_client.chat.completions.create.return_value = mock_stream
        
        # Measure streaming latency
        generator = vllm_service.clean_markdown_content_stream("Test")
        
        start_time = time.time()
        first_token = next(generator)
        first_token_time = time.time() - start_time
        
        # First token should arrive quickly (not wait for all tokens)
        assert first_token_time < 0.05  # Should be almost immediate
        assert first_token == "First"
    
    def test_streaming_memory_efficiency(self):
        """Test that streaming doesn't buffer large amounts"""
        def large_generator():
            for i in range(1000):
                yield f"chunk_{i}"
        
        # Streaming should not load all chunks into memory
        generator = large_generator()
        
        # Get first few chunks
        chunks = []
        for i, chunk in enumerate(generator):
            chunks.append(chunk)
            if i >= 5:
                break
        
        assert len(chunks) == 6
        assert chunks[0] == "chunk_0"
        assert chunks[5] == "chunk_5"
        
        # Generator should still have more items (not exhausted)
        next_chunk = next(generator)
        assert next_chunk == "chunk_6"


class TestStreamingErrorHandling:
    """Test error handling in streaming"""
    
    @patch('services.VLLMService.client')
    def test_streaming_error_recovery(self, mock_client):
        """Test error handling during streaming"""
        vllm_service = VLLMService()
        
        # Mock stream that raises error
        def error_chunks():
            yield Mock(choices=[Mock(delta=Mock(content="Good"), finish_reason=None)])
            raise Exception("Stream error")
        
        mock_stream = Mock()
        mock_stream.__iter__ = Mock(return_value=error_chunks())
        mock_client.chat.completions.create.return_value = mock_stream
        
        # Should handle error gracefully
        generator = vllm_service.clean_markdown_content_stream("Test")
        
        # First chunk should work
        first_chunk = next(generator)
        assert first_chunk == "Good"
        
        # Second chunk should raise error
        with pytest.raises(Exception):
            next(generator)
    
    @patch('vllm_manager.vllm_manager._is_vllm_running')
    def test_streaming_vllm_unavailable(self, mock_vllm_running):
        """Test streaming when vLLM is unavailable"""
        mock_vllm_running.return_value = False
        
        client = TestClient(app)
        response = client.post(
            "/clean-markdown-stream",
            json={"markdown_content": "Test content"}
        )
        
        assert response.status_code == 503
        assert "vLLM" in response.json()["detail"]


class TestStreamingIntegration:
    """Integration tests for streaming functionality"""
    
    @pytest.mark.asyncio
    async def test_streaming_with_httpx_client(self):
        """Test streaming with real HTTP client"""
        # This would test against a real server
        # Skip if server not available
        pytest.skip("Integration test - requires running server")
    
    def test_streaming_response_headers(self):
        """Test that streaming responses have correct headers"""
        def test_generator():
            yield "test"
        
        response = StreamingResponse(test_generator(), media_type="text/plain; charset=utf-8")
        
        # Test that we can create streaming response
        assert response.media_type == "text/plain; charset=utf-8"
    
    def test_streaming_content_type_utf8(self):
        """Test that streaming responses specify UTF-8 encoding"""
        client = TestClient(app)
        
        with patch('vllm_manager.vllm_manager._is_vllm_running', return_value=True), \
             patch('services.VLLMService.clean_markdown_content_stream', return_value=iter(["test"])):
            
            response = client.post(
                "/clean-markdown-stream",
                json={"markdown_content": "Test content"}
            )
            
            content_type = response.headers.get("content-type", "")
            assert "charset=utf-8" in content_type 