import logging
import tempfile
import os
from typing import Optional, Dict, Any
from io import BytesIO

import httpx
from openai import OpenAI
from markitdown import MarkItDown

from config import settings

logger = logging.getLogger(__name__)


class PDFConverterService:
    """Service for converting PDF files to Markdown"""
    
    def __init__(self):
        self.md_converter = MarkItDown()
    
    async def convert_pdf_to_markdown(self, file_content: bytes, filename: str) -> str:
        """
        Convert PDF file content to Markdown format
        
        Args:
            file_content: PDF file content as bytes
            filename: Original filename for logging
            
        Returns:
            Markdown content as string
            
        Raises:
            Exception: If conversion fails
        """
        logger.info(f"Converting PDF to Markdown: {filename}")
        
        # Create temporary file for MarkItDown processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Convert PDF to Markdown using MarkItDown
            result = self.md_converter.convert(temp_file_path)
            
            if not result or not result.text_content:
                raise Exception("Failed to extract content from PDF")
            
            markdown_content = result.text_content
            logger.info(f"Successfully converted {filename} to Markdown ({len(markdown_content)} characters)")
            
            return markdown_content
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass


class VLLMService:
    """Service for interacting with vLLM for content cleaning"""
    
    def __init__(self):
        self.client = OpenAI(
            base_url=f"{settings.vllm_base_url}/v1",
            api_key="not-needed"  # vLLM doesn't require API key when running locally
        )
    
    async def test_connection(self) -> bool:
        """Test if vLLM service is reachable"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{settings.vllm_base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"vLLM connection test failed: {e}")
            return False
    
    async def clean_markdown_content(self, markdown_content: str) -> str:
        """
        Clean and improve markdown content using vLLM
        
        Args:
            markdown_content: Raw markdown content to clean
            
        Returns:
            Cleaned markdown content
            
        Raises:
            Exception: If cleaning fails
        """
        try:
            system_prompt = self._get_cleaning_system_prompt()
            user_prompt = f"Please clean and improve this markdown content:\n\n{markdown_content}"

            response = self.client.chat.completions.create(
                model=settings.vllm_model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=settings.vllm_max_tokens,
                temperature=settings.vllm_temperature,
                stream=False
            )
            
            cleaned_content = response.choices[0].message.content
            logger.info("Successfully cleaned markdown content with vLLM")
            return cleaned_content
            
        except Exception as e:
            logger.error(f"Error cleaning markdown with vLLM: {e}")
            raise
    
    def _get_cleaning_system_prompt(self) -> str:
        """Get the system prompt for markdown cleaning"""
        return """You are an expert text processor. Your task is to clean and improve markdown content that was converted from PDF.

Please:
1. Fix any obvious OCR errors and garbled text
2. Improve formatting and structure
3. Ensure proper markdown syntax
4. Remove excessive whitespace and fix line breaks
5. Keep the content meaning intact
6. Maintain the original language of the document
7. Fix broken tables and lists
8. Correct heading hierarchies
9. Remove artifacts from PDF conversion

Return only the cleaned markdown content without any additional commentary or explanations."""


class DocumentProcessingService:
    """Main service orchestrating PDF conversion and cleaning"""
    
    def __init__(self):
        self.pdf_service = PDFConverterService()
        self.vllm_service = VLLMService()
    
    async def process_document(
        self, 
        file_content: bytes, 
        filename: str, 
        clean_with_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Process a PDF document: convert to markdown and optionally clean with LLM
        
        Args:
            file_content: PDF file content as bytes
            filename: Original filename
            clean_with_llm: Whether to clean content with vLLM
            
        Returns:
            Dictionary with processing results
        """
        # Convert PDF to Markdown
        raw_markdown = await self.pdf_service.convert_pdf_to_markdown(
            file_content, filename
        )
        
        # Clean with vLLM if requested
        final_markdown = raw_markdown
        cleaned_with_llm = False
        
        if clean_with_llm:
            try:
                logger.info("Cleaning markdown content with vLLM")
                final_markdown = await self.vllm_service.clean_markdown_content(raw_markdown)
                cleaned_with_llm = final_markdown != raw_markdown
            except Exception as e:
                logger.warning(f"vLLM cleaning failed, using raw markdown: {e}")
                # Continue with raw markdown if cleaning fails
        
        return {
            "success": True,
            "filename": filename,
            "raw_markdown": raw_markdown,
            "cleaned_markdown": final_markdown,
            "cleaned_with_llm": cleaned_with_llm,
            "content_length": len(final_markdown),
            "metadata": {
                "original_filename": filename,
                "file_size_bytes": len(file_content),
                "conversion_method": "MarkItDown",
                "llm_cleaning": clean_with_llm
            }
        }
    
    async def get_health_status(self) -> Dict[str, str]:
        """Get health status of all services"""
        health_status = {
            "api": "healthy",
            "vllm": "unknown"
        }
        
        try:
            vllm_healthy = await self.vllm_service.test_connection()
            health_status["vllm"] = "healthy" if vllm_healthy else "unhealthy"
        except Exception as e:
            health_status["vllm"] = f"error: {str(e)}"
            logger.error(f"vLLM health check failed: {e}")
        
        return health_status


# Global service instances
document_service = DocumentProcessingService() 