#!/usr/bin/env python3
"""
Test script for streaming endpoints
Demonstrates token-by-token streaming from vLLM
"""

import asyncio
import httpx
import json
from pathlib import Path


async def test_markdown_streaming():
    """Test streaming markdown cleaning"""
    print("🚀 Testing Markdown Streaming Endpoint")
    print("=" * 50)
    
    # Sample markdown content
    sample_markdown = """
# Document Title

This is a test document with some poorly formatted content.
There are    extra   spaces and 

unnecessary line breaks.

## Section 1
- Item one
- Item  two   
- Item three

The formatting needs improvement and this content should be cleaned up by the LLM.
"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            payload = {"markdown_content": sample_markdown}
            
            print(f"📤 Sending request to /clean-markdown-stream...")
            print(f"Content length: {len(sample_markdown)} characters")
            print("\n🔄 Streaming response:")
            print("-" * 30)
            
            async with client.stream(
                "POST", 
                "http://localhost:8001/clean-markdown-stream",
                json=payload
            ) as response:
                
                if response.status_code != 200:
                    print(f"❌ Error: {response.status_code}")
                    print(f"Response: {await response.aread()}")
                    return
                
                # Stream tokens
                full_response = ""
                async for chunk in response.aiter_text():
                    if chunk:
                        print(chunk, end="", flush=True)
                        full_response += chunk
                
                print("\n" + "-" * 30)
                print(f"✅ Streaming complete!")
                print(f"📊 Total response length: {len(full_response)} characters")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_pdf_streaming():
    """Test streaming PDF upload and cleaning"""
    print("\n🚀 Testing PDF Upload Streaming Endpoint")
    print("=" * 50)
    
    # Look for a sample PDF file
    pdf_paths = [
        "../AlexNet.pdf",
        "../../AlexNet.pdf", 
        "../test.pdf",
        "test.pdf"
    ]
    
    pdf_file = None
    for path in pdf_paths:
        if Path(path).exists():
            pdf_file = Path(path)
            break
    
    if not pdf_file:
        print("❌ No PDF file found for testing")
        print(f"Looked for: {pdf_paths}")
        return
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            print(f"📤 Uploading PDF: {pdf_file.name} ({pdf_file.stat().st_size / 1024:.1f} KB)")
            
            with open(pdf_file, 'rb') as f:
                files = {'file': (pdf_file.name, f, 'application/pdf')}
                
                print("\n🔄 Streaming response:")
                print("-" * 30)
                
                async with client.stream(
                    "POST",
                    "http://localhost:8001/upload-stream",
                    files=files
                ) as response:
                    
                    if response.status_code != 200:
                        print(f"❌ Error: {response.status_code}")
                        print(f"Response: {await response.aread()}")
                        return
                    
                    # Stream tokens
                    full_response = ""
                    chunk_count = 0
                    async for chunk in response.aiter_text():
                        if chunk:
                            # Show first few chunks, then show progress
                            if chunk_count < 100:
                                print(chunk, end="", flush=True)
                            elif chunk_count % 50 == 0:
                                print(".", end="", flush=True)
                            
                            full_response += chunk
                            chunk_count += 1
                    
                    print("\n" + "-" * 30)
                    print(f"✅ Streaming complete!")
                    print(f"📊 Total chunks received: {chunk_count}")
                    print(f"📊 Total response length: {len(full_response)} characters")
                    
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_streaming_comparison():
    """Compare streaming vs non-streaming endpoints"""
    print("\n🚀 Testing Streaming vs Non-Streaming Comparison")
    print("=" * 50)
    
    sample_content = "# Test\n\nThis is a simple test document for comparing streaming vs non-streaming responses."
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            payload = {"markdown_content": sample_content}
            
            # Test non-streaming endpoint
            print("📤 Testing non-streaming endpoint...")
            import time
            start_time = time.time()
            
            response = await client.post(
                "http://localhost:8001/clean-markdown",
                json=payload
            )
            
            non_streaming_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Non-streaming response received in {non_streaming_time:.2f}s")
                print(f"📊 Content length: {len(data['cleaned_content'])} characters")
                non_streaming_content = data['cleaned_content']
            else:
                print(f"❌ Non-streaming failed: {response.status_code}")
                return
            
            # Test streaming endpoint
            print("\n📤 Testing streaming endpoint...")
            start_time = time.time()
            
            async with client.stream(
                "POST",
                "http://localhost:8001/clean-markdown-stream", 
                json=payload
            ) as stream_response:
                
                if stream_response.status_code != 200:
                    print(f"❌ Streaming failed: {stream_response.status_code}")
                    return
                
                streaming_content = ""
                first_token_time = None
                
                async for chunk in stream_response.aiter_text():
                    if chunk and first_token_time is None:
                        first_token_time = time.time() - start_time
                    streaming_content += chunk
                
                total_streaming_time = time.time() - start_time
                
                print(f"✅ Streaming response completed in {total_streaming_time:.2f}s")
                print(f"⚡ First token received in {first_token_time:.2f}s")
                print(f"📊 Content length: {len(streaming_content)} characters")
                
                # Compare content
                print(f"\n📊 Comparison:")
                print(f"- Non-streaming time: {non_streaming_time:.2f}s")
                print(f"- Streaming total time: {total_streaming_time:.2f}s")
                print(f"- Time to first token: {first_token_time:.2f}s")
                print(f"- Content matches: {non_streaming_content.strip() == streaming_content.strip()}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Run all streaming tests"""
    print("🧪 vLLM Streaming Test Suite")
    print("=" * 50)
    
    # Check if API is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/health")
            if response.status_code != 200:
                print("❌ API is not running. Please start the backend first.")
                return
            
            health_data = response.json()
            print(f"✅ API is running")
            print(f"📊 vLLM status: {health_data.get('vllm', 'unknown')}")
            
            if health_data.get('vllm') != 'healthy':
                print("⚠️  vLLM service may not be available. Some tests might fail.")
    
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Run tests
    await test_markdown_streaming()
    await test_pdf_streaming() 
    await test_streaming_comparison()
    
    print("\n🎉 All streaming tests completed!")


if __name__ == "__main__":
    asyncio.run(main()) 