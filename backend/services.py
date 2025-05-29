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

            # Estimate token count and adjust max_tokens if needed
            estimated_input_tokens = self._estimate_token_count(system_prompt + user_prompt)
            max_tokens = min(
                settings.vllm_max_tokens,
                settings.vllm_max_model_len - estimated_input_tokens - 100  # Leave 100 token buffer
            )
            
            if max_tokens < 500:
                raise Exception(f"Input too long: estimated {estimated_input_tokens} tokens, "
                              f"leaving only {max_tokens} tokens for response")

            response = self.client.chat.completions.create(
                model=settings.vllm_model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=settings.vllm_temperature,
                stream=False
            )
            
            cleaned_content = response.choices[0].message.content
            logger.info(f"Successfully cleaned markdown content with vLLM (used {max_tokens} max_tokens)")
            return cleaned_content
            
        except Exception as e:
            logger.error(f"Error cleaning markdown with vLLM: {e}")
            raise

    def clean_markdown_content_stream(self, markdown_content: str):
        """
        Clean and improve markdown content using vLLM with streaming response
        
        Args:
            markdown_content: Raw markdown content to clean
            
        Yields:
            str: Token by token response from vLLM
            
        Raises:
            Exception: If cleaning fails
        """
        try:
            # Use proper Qwen3 system message format
            system_prompt = "Clean and format the provided markdown text. Fix any formatting errors, OCR mistakes, and improve structure. Output only the cleaned markdown without explanations."
            user_prompt = f"Clean this markdown content:\n\n{markdown_content}"

            # Estimate token count and adjust max_tokens if needed
            estimated_input_tokens = self._estimate_token_count(system_prompt + user_prompt)
            max_tokens = min(
                settings.vllm_max_tokens,
                settings.vllm_max_model_len - estimated_input_tokens - 100  # Leave 100 token buffer
            )
            
            if max_tokens < 500:
                raise Exception(f"Input too long: estimated {estimated_input_tokens} tokens, "
                              f"leaving only {max_tokens} tokens for response")

            logger.info(f"Starting streaming markdown cleaning with vLLM (max_tokens: {max_tokens}, no-thinking mode)")
            
            # Create streaming response with Qwen3 non-thinking mode settings
            # According to Qwen3 docs: For non-thinking mode, use Temperature=0.7, TopP=0.8, TopK=20
            stream = self.client.chat.completions.create(
                model=settings.vllm_model_name,
                messages=[
                    {"role": "system", "content": "You are a text formatter. Respond directly without thinking. /no_think"},
                    {"role": "user", "content": f"/no_think Clean this markdown:\n\n{markdown_content}"}
                ],
                max_tokens=max_tokens,
                temperature=0.7,  # Qwen3 recommended for non-thinking mode
                top_p=0.8,        # Qwen3 recommended for non-thinking mode
                stream=True,
                stream_options={"include_usage": False}
            )
            
            logger.info(f"Stream object created, starting token iteration...")
            token_count = 0
            thinking_mode = False
            buffer = ""
            
            # IMPORTANT: Use sync iteration, not async - this was the bug!
            try:
                for chunk in stream:  # NOT async for!
                    if chunk.choices and len(chunk.choices) > 0:
                        choice = chunk.choices[0]
                        if choice.delta and choice.delta.content is not None:
                            content = choice.delta.content
                            buffer += content
                            
                            # Handle thinking tags - filter them out
                            if "<think>" in buffer:
                                thinking_mode = True
                                # Remove everything up to and including <think>
                                buffer = buffer.split("<think>", 1)[-1]
                                continue
                            elif "</think>" in buffer and thinking_mode:
                                thinking_mode = False
                                # Remove everything up to and including </think>
                                parts = buffer.split("</think>", 1)
                                if len(parts) > 1:
                                    buffer = parts[1]
                                else:
                                    buffer = ""
                                # Continue to process any remaining content
                                if buffer.strip():
                                    token_count += 1
                                    logger.debug(f"Yielding token {token_count}: '{buffer[:20]}...'")
                                    yield buffer
                                    buffer = ""
                                continue
                            elif thinking_mode:
                                # Skip content while in thinking mode
                                buffer = ""
                                continue
                            else:
                                # Normal content - yield it
                                token_count += 1
                                logger.debug(f"Yielding token {token_count}: '{content[:20]}...'")
                                yield content
                                buffer = ""
                                
                        elif choice.finish_reason:
                            logger.info(f"Stream finished with reason: {choice.finish_reason}")
                            # Yield any remaining buffer content
                            if buffer.strip() and not thinking_mode:
                                yield buffer
                            break
                    else:
                        logger.debug("Received chunk with no choices")
                        
            except Exception as stream_error:
                logger.error(f"Error during streaming iteration: {stream_error}")
                raise
                
            logger.info(f"Streaming completed. Total tokens yielded: {token_count}")
                    
        except Exception as e:
            logger.error(f"Error streaming markdown cleaning with vLLM: {e}")
            raise

    def _get_cleaning_system_prompt(self) -> str:
        """Get the system prompt for markdown cleaning"""
        return """Fix formatting and clean the text. Output the corrected version immediately without any explanation."""

    def _estimate_token_count(self, text: str) -> int:
        """
        Rough estimation of token count (approximately 4 characters per token)
        This is a simple approximation - in production you might want to use tiktoken
        """
        return len(text) // 4


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