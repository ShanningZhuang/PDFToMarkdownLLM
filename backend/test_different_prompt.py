#!/usr/bin/env python3
"""
Test different prompts to find one that streams well
"""

import asyncio
import httpx
import time
from openai import OpenAI
from config import settings


async def test_simple_prompt():
    """Test with a very simple prompt that should stream well"""
    print("🔍 Testing Simple Counting Prompt")
    print("=" * 40)
    
    client = OpenAI(
        base_url=f"{settings.vllm_base_url}/v1",
        api_key="not-needed"
    )
    
    try:
        start_time = time.time()
        
        stream = client.chat.completions.create(
            model=settings.vllm_model_name,
            messages=[
                {"role": "user", "content": "Please count from 1 to 10, one number per line."}
            ],
            max_tokens=100,
            temperature=0.3,  # Higher temperature for better streaming
            stream=True
        )
        
        print("🔄 Direct streaming response:")
        token_count = 0
        
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token_count += 1
                elapsed = time.time() - start_time
                content = chunk.choices[0].delta.content
                print(f"[{elapsed:.3f}s] {repr(content)}", end="", flush=True)
                
                if token_count >= 20:  # Limit output
                    print("\n... (continuing)")
                    break
        
        print(f"\n📊 Received {token_count} tokens - {'✅ STREAMING!' if token_count > 5 else '❌ Not streaming well'}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


async def test_markdown_simple_api():
    """Test our API with very simple markdown"""
    print("\n🔍 Testing API with Simple Content")
    print("=" * 40)
    
    simple_content = "Fix this text."
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            payload = {"markdown_content": simple_content}
            print(f"📤 Testing with: {repr(simple_content)}")
            
            start_time = time.time()
            
            async with client.stream(
                "POST", 
                "http://localhost:8001/clean-markdown-stream",
                json=payload
            ) as response:
                
                if response.status_code != 200:
                    error_content = await response.aread()
                    print(f"❌ Error {response.status_code}: {error_content}")
                    return
                
                print("🔄 API Response:")
                chunks = []
                
                async for chunk in response.aiter_text():
                    if chunk:
                        elapsed = time.time() - start_time
                        chunks.append(chunk)
                        print(f"[{elapsed:.3f}s] {repr(chunk[:50])}")
                
                print(f"\n📊 Received {len(chunks)} chunks - {'✅ STREAMING!' if len(chunks) > 2 else '❌ Not streaming well'}")
                print(f"Full response: {repr(''.join(chunks)[:100])}")
                
        except Exception as e:
            print(f"❌ API test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_simple_prompt())
    asyncio.run(test_markdown_simple_api()) 