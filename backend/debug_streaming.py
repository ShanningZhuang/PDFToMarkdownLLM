#!/usr/bin/env python3
"""
Debug script to test vLLM streaming directly
This helps identify where streaming might be breaking
"""

import asyncio
import httpx
import time
import json
from openai import OpenAI
from config import settings


async def test_direct_vllm_streaming():
    """Test streaming directly with vLLM using OpenAI client"""
    print("🔍 Testing Direct vLLM Streaming")
    print("=" * 50)
    
    client = OpenAI(
        base_url=f"{settings.vllm_base_url}/v1",
        api_key="not-needed"
    )
    
    test_content = "# Test Document\n\nThis is a simple test for streaming."
    
    try:
        print(f"📤 Sending streaming request to vLLM...")
        start_time = time.time()
        
        stream = client.chat.completions.create(
            model=settings.vllm_model_name,
            messages=[
                {"role": "system", "content": "Clean and improve this markdown content."},
                {"role": "user", "content": f"Please clean: {test_content}"}
            ],
            max_tokens=1000,
            temperature=0.1,
            stream=True,
            stream_options={"include_usage": False}
        )
        
        print("🔄 Streaming response:")
        print("-" * 30)
        
        token_count = 0
        first_token_time = None
        
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                if choice.delta and choice.delta.content is not None:
                    if first_token_time is None:
                        first_token_time = time.time() - start_time
                        print(f"\n⚡ First token received in {first_token_time:.3f}s")
                        print("Content: ", end="")
                    
                    content = choice.delta.content
                    print(content, end="", flush=True)
                    token_count += 1
                elif choice.finish_reason:
                    print(f"\n🏁 Stream finished: {choice.finish_reason}")
                    break
        
        total_time = time.time() - start_time
        print(f"\n📊 Total tokens: {token_count}, Total time: {total_time:.3f}s")
        
    except Exception as e:
        print(f"❌ Direct streaming failed: {e}")


async def test_api_streaming():
    """Test streaming through our API endpoint"""
    print("\n🔍 Testing API Streaming Endpoint")
    print("=" * 50)
    
    test_content = "# Test Document\n\nThis is a simple test for API streaming."
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            payload = {"markdown_content": test_content}
            print(f"📤 Sending request to /clean-markdown-stream...")
            
            start_time = time.time()
            
            async with client.stream(
                "POST", 
                "http://localhost:8001/clean-markdown-stream",
                json=payload
            ) as response:
                
                print(f"📊 Response status: {response.status_code}")
                print(f"📊 Response headers: {dict(response.headers)}")
                
                if response.status_code != 200:
                    error_content = await response.aread()
                    print(f"❌ Error response: {error_content}")
                    return
                
                print("🔄 Streaming response:")
                print("-" * 30)
                
                chunk_count = 0
                first_chunk_time = None
                full_response = ""
                
                async for chunk in response.aiter_text():
                    if chunk:
                        if first_chunk_time is None:
                            first_chunk_time = time.time() - start_time
                            print(f"\n⚡ First chunk received in {first_chunk_time:.3f}s")
                            print("Content: ", end="")
                        
                        print(chunk, end="", flush=True)
                        full_response += chunk
                        chunk_count += 1
                
                total_time = time.time() - start_time
                print(f"\n📊 Total chunks: {chunk_count}, Total time: {total_time:.3f}s")
                print(f"📊 Response length: {len(full_response)} characters")
                
        except Exception as e:
            print(f"❌ API streaming failed: {e}")


async def test_http_streaming_raw():
    """Test raw HTTP streaming to see exact response format"""
    print("\n🔍 Testing Raw HTTP Streaming")
    print("=" * 50)
    
    test_content = "# Test\n\nSimple test."
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            payload = {"markdown_content": test_content}
            
            async with client.stream(
                "POST", 
                "http://localhost:8001/clean-markdown-stream",
                json=payload
            ) as response:
                
                print(f"📊 Status: {response.status_code}")
                print(f"📊 Headers:")
                for key, value in response.headers.items():
                    print(f"   {key}: {value}")
                
                if response.status_code != 200:
                    return
                
                print("\n🔍 Raw chunks:")
                print("-" * 30)
                
                chunk_num = 0
                async for chunk in response.aiter_bytes():
                    chunk_num += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    print(f"Chunk {chunk_num} ({len(chunk)} bytes): {repr(chunk_text[:50])}")
                    
                    if chunk_num >= 10:  # Limit output
                        print("... (truncated)")
                        break
                
        except Exception as e:
            print(f"❌ Raw streaming failed: {e}")


async def test_vllm_health():
    """Test if vLLM is running and healthy"""
    print("\n🔍 Testing vLLM Health")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Test health endpoint
            response = await client.get(f"{settings.vllm_base_url}/health")
            print(f"📊 vLLM health: {response.status_code}")
            
            # Test models endpoint
            response = await client.get(f"{settings.vllm_base_url}/v1/models")
            if response.status_code == 200:
                models = response.json()
                print(f"📊 Available models: {[m['id'] for m in models.get('data', [])]}")
            
            # Test simple completion
            response = await client.post(
                f"{settings.vllm_base_url}/v1/chat/completions",
                json={
                    "model": settings.vllm_model_name,
                    "messages": [{"role": "user", "content": "Say 'test'"}],
                    "max_tokens": 10,
                    "stream": False
                }
            )
            print(f"📊 Simple completion: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                print(f"📊 Response: {content}")
            
        except Exception as e:
            print(f"❌ vLLM health check failed: {e}")


async def main():
    """Run all diagnostic tests"""
    print("🧪 vLLM Streaming Diagnostics")
    print("=" * 50)
    
    # Test vLLM health first
    await test_vllm_health()
    
    # Test direct streaming
    await test_direct_vllm_streaming()
    
    # Test API streaming
    await test_api_streaming()
    
    # Test raw HTTP streaming
    await test_http_streaming_raw()
    
    print("\n🎉 Diagnostics completed!")


if __name__ == "__main__":
    asyncio.run(main()) 