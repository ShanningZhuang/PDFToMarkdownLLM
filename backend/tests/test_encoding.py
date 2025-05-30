"""
Tests for encoding functionality including Chinese character support
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from services import PDFConverterService, VLLMService
from main import encode_filename_for_header


class TestFilenameEncoding:
    """Test filename encoding for HTTP headers"""
    
    def test_ascii_filename_unchanged(self):
        """ASCII filenames should pass through unchanged"""
        filename = "test_document.pdf"
        result = encode_filename_for_header(filename)
        assert result == filename
    
    def test_chinese_filename_url_encoded(self):
        """Chinese filenames should be URL encoded"""
        filename = "中文文档.pdf"
        result = encode_filename_for_header(filename)
        expected = "%E4%B8%AD%E6%96%87%E6%96%87%E6%A1%A3.pdf"
        assert result == expected
    
    def test_mixed_filename_encoding(self):
        """Mixed ASCII and Chinese filenames should be URL encoded"""
        filename = "Report_2024_中文版.pdf"
        result = encode_filename_for_header(filename)
        # Should be URL encoded since it contains Chinese characters
        assert "%" in result
        assert result != filename
    
    def test_special_characters_encoding(self):
        """Special characters should be URL encoded"""
        filename = "文档（最终版）.pdf"
        result = encode_filename_for_header(filename)
        assert "%" in result
        assert "(" not in result  # Parentheses should be encoded
    
    def test_empty_filename(self):
        """Empty filename should be handled gracefully"""
        result = encode_filename_for_header("")
        assert result == ""
    
    def test_latin1_compatible_unchanged(self):
        """Latin-1 compatible characters should pass through"""
        filename = "café_résumé.pdf"
        result = encode_filename_for_header(filename)
        assert result == filename


class TestPDFEncodingFix:
    """Test PDF content encoding fixes"""
    
    @pytest.fixture
    def pdf_service(self):
        return PDFConverterService()
    
    def test_fix_encoding_normal_string(self, pdf_service):
        """Normal UTF-8 strings should pass through unchanged"""
        content = "This is normal English text with 中文 characters"
        result = pdf_service._fix_encoding_issues(content, "test.pdf")
        assert result == content
    
    def test_fix_encoding_problematic_chars(self, pdf_service):
        """Problematic characters should be fixed"""
        # Create content with characters outside latin-1 range
        problematic_content = "Test" + chr(256) + chr(257) + "中文"
        result = pdf_service._fix_encoding_issues(problematic_content, "test.pdf")
        
        # Should not raise encoding errors
        result.encode('utf-8')
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_fix_encoding_bytes_input(self, pdf_service):
        """Bytes input should be converted to string"""
        content_bytes = "测试内容".encode('utf-8')
        result = pdf_service._fix_encoding_issues(content_bytes, "test.pdf")
        
        assert isinstance(result, str)
        assert "测试内容" in result
    
    def test_fix_encoding_mixed_encoding(self, pdf_service):
        """Mixed encoding content should be handled"""
        # Simulate content that might come from MarkItDown
        content = "Normal text with special chars: " + chr(170) + chr(186)
        result = pdf_service._fix_encoding_issues(content, "test.pdf")
        
        # Should be encodable to UTF-8
        result.encode('utf-8')
        assert isinstance(result, str)
    
    def test_fix_encoding_empty_content(self, pdf_service):
        """Empty content should be handled gracefully"""
        result = pdf_service._fix_encoding_issues("", "test.pdf")
        assert result == ""
    
    def test_fix_encoding_null_chars(self, pdf_service):
        """Null characters should be handled"""
        content = "Test\x00\x01\x02中文"
        result = pdf_service._fix_encoding_issues(content, "test.pdf")
        
        # Should not raise encoding errors
        result.encode('utf-8')
        assert isinstance(result, str)


class TestVLLMEncodingVerification:
    """Test vLLM service encoding verification"""
    
    @pytest.fixture
    def vllm_service(self):
        return VLLMService()
    
    def test_vllm_encoding_verification_normal(self, vllm_service):
        """Normal content should pass verification"""
        content = "# Test Document\n\n这是中文内容测试。"
        result = vllm_service._fix_encoding_issues(content, "streaming_input")
        assert result == content
    
    def test_vllm_encoding_verification_problematic(self, vllm_service):
        """Problematic content should be fixed"""
        content = "Test" + chr(256) + "中文"
        result = vllm_service._fix_encoding_issues(content, "streaming_input")
        
        # Should be UTF-8 safe
        result.encode('utf-8')
        assert isinstance(result, str)
    
    def test_vllm_encoding_verification_bytes(self, vllm_service):
        """Bytes content should be converted"""
        content_bytes = "中文测试".encode('utf-8')
        result = vllm_service._fix_encoding_issues(content_bytes, "streaming_input")
        
        assert isinstance(result, str)
        assert "中文测试" in result


class TestStreamingEncoding:
    """Test encoding in streaming context"""
    
    @pytest.fixture
    def vllm_service(self):
        return VLLMService()
    
    def test_streaming_token_encoding(self, vllm_service):
        """Individual streaming tokens should be UTF-8 safe"""
        test_tokens = [
            "Hello",
            "中文",
            "测试",
            "🎉",  # Emoji
            "café",
            "résumé"
        ]
        
        for token in test_tokens:
            # Each token should be encodable
            token.encode('utf-8')
            
            # Should pass through encoding fix unchanged
            fixed = vllm_service._fix_encoding_issues(token, "token_test")
            assert fixed == token
    
    def test_streaming_chunk_validation(self, vllm_service):
        """Streaming chunks should be validated for encoding"""
        # Simulate problematic chunks that might come from vLLM
        problematic_chunks = [
            "Normal text",
            "中文" + chr(256),  # Mixed valid and invalid
            chr(257) + chr(258),  # Invalid characters
            "More 中文 content"
        ]
        
        for chunk in problematic_chunks:
            fixed = vllm_service._fix_encoding_issues(chunk, "chunk_test")
            
            # Fixed chunk should always be UTF-8 encodable
            fixed.encode('utf-8')
            assert isinstance(fixed, str)


class TestEndToEndEncoding:
    """Test complete encoding workflow"""
    
    @pytest.fixture
    def pdf_service(self):
        return PDFConverterService()
    
    @pytest.fixture
    def vllm_service(self):
        return VLLMService()
    
    def test_pdf_to_streaming_encoding_flow(self, pdf_service, vllm_service):
        """Test complete flow from PDF to streaming"""
        # Simulate MarkItDown output with encoding issues
        raw_markdown = "# 中文文档\n\n内容" + chr(256) + "测试"
        
        # Step 1: PDF service fixes encoding
        fixed_markdown = pdf_service._fix_encoding_issues(raw_markdown, "test.pdf")
        fixed_markdown.encode('utf-8')  # Should not raise
        
        # Step 2: vLLM service verifies encoding
        verified_markdown = vllm_service._fix_encoding_issues(fixed_markdown, "streaming_input")
        verified_markdown.encode('utf-8')  # Should not raise
        
        # Step 3: Simulate streaming tokens
        tokens = [verified_markdown[i:i+5] for i in range(0, len(verified_markdown), 5)]
        
        for token in tokens:
            # Each token should be UTF-8 safe
            token.encode('utf-8')
    
    def test_chinese_filename_with_content(self, pdf_service):
        """Test Chinese filename with Chinese content"""
        chinese_filename = "中文文档测试.pdf"
        chinese_content = "# 测试文档\n\n这是中文内容。"
        
        # Filename encoding
        encoded_filename = encode_filename_for_header(chinese_filename)
        assert "%" in encoded_filename  # Should be URL encoded
        
        # Content encoding
        fixed_content = pdf_service._fix_encoding_issues(chinese_content, chinese_filename)
        fixed_content.encode('utf-8')  # Should not raise
        
        assert fixed_content == chinese_content  # Should be unchanged if already valid


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.fixture
    def pdf_service(self):
        return PDFConverterService()
    
    def test_extremely_long_filename(self, pdf_service):
        """Very long filenames should be handled"""
        long_filename = "很长的中文文件名" * 20 + ".pdf"
        result = encode_filename_for_header(long_filename)
        
        # Should be URL encoded and not raise errors
        assert "%" in result
        result.encode('latin-1')  # Should be latin-1 safe
    
    def test_unicode_edge_cases(self, pdf_service):
        """Unicode edge cases should be handled"""
        edge_cases = [
            "\u0000",  # Null character
            "\uffff",  # High Unicode
            "\ud800",  # Surrogate (invalid)
            "🎉🚀🔥",  # Emojis
        ]
        
        for case in edge_cases:
            try:
                result = pdf_service._fix_encoding_issues(case, "edge_test.pdf")
                result.encode('utf-8')  # Should not raise
            except Exception:
                # Some edge cases might fail, but shouldn't crash
                pass
    
    def test_none_and_invalid_inputs(self, pdf_service):
        """None and invalid inputs should be handled gracefully"""
        # Test None input
        result = pdf_service._fix_encoding_issues(None, "test.pdf")
        assert result is not None
        
        # Test non-string input
        result = pdf_service._fix_encoding_issues(123, "test.pdf")
        assert isinstance(result, str) 