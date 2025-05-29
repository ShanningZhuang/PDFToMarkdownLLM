#!/usr/bin/env python3
"""
Simple streaming test to quickly verify if token-by-token streaming works
"""

import asyncio
import httpx
import time


async def quick_stream_test():
    """Quick test of streaming endpoint"""
    print("🚀 Quick Streaming Test")
    print("=" * 30)
    
    # Simple, short content to minimize processing time
    test_content = "# Test\n\nFix this."
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            payload = {"markdown_content": test_content}
            print(f"📤 Testing with: {repr(test_content)}")
            
            start_time = time.time()
            
            async with client.stream(
                "POST", 
                "http://localhost:8001/clean-markdown-stream",
                json=payload
            ) as response:
                
                if response.status_code != 200:
                    print(f"❌ Error {response.status_code}: {await response.aread()}")
                    return
                
                print(f"📊 Status: {response.status_code}")
                print(f"📊 Headers: {dict(response.headers)}")
                print("\n🔄 Response:")
                
                chunk_times = []
                chunks = []
                
                async for chunk in response.aiter_text():
                    if chunk:
                        chunk_time = time.time() - start_time
                        chunk_times.append(chunk_time)
                        chunks.append(chunk)
                        
                        print(f"[{chunk_time:.3f}s] {repr(chunk)}")
                
                total_time = time.time() - start_time
                print(f"\n📊 Summary:")
                print(f"   Total chunks: {len(chunks)}")
                print(f"   Total time: {total_time:.3f}s")
                print(f"   Full response: {repr(''.join(chunks))}")
                
                if len(chunks) > 1:
                    print("✅ STREAMING WORKS! Multiple chunks received")
                    print(f"   Time between chunks: {[f'{chunk_times[i] - chunk_times[i-1]:.3f}s' for i in range(1, len(chunk_times))]}")
                else:
                    print("❌ NOT STREAMING - Only one chunk received")
                    print("   This suggests buffering is happening somewhere")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")


async def test_direct_vllm():
    """Test direct vLLM streaming to isolate the issue"""
    print("\n🔧 Direct vLLM Test")
    print("=" * 30)
    
    from openai import OpenAI
    from config import settings
    
    client = OpenAI(
        base_url=f"{settings.vllm_base_url}/v1",
        api_key="not-needed"
    )
    
    try:
        print("📤 Testing direct vLLM streaming...")
        start_time = time.time()
        
        stream = client.chat.completions.create(
            model=settings.vllm_model_name,
            messages=[
                {"role": "user", "content": "Count from 1 to 5, one number per line."}
            ],
            max_tokens=50,
            temperature=0.1,
            stream=True
        )
        
        print("🔄 Direct vLLM response:")
        chunk_count = 0
        
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                chunk_count += 1
                elapsed = time.time() - start_time
                content = chunk.choices[0].delta.content
                print(f"[{elapsed:.3f}s] Chunk {chunk_count}: {repr(content)}")
        
        print(f"\n📊 Direct vLLM: {chunk_count} chunks received")
        
        if chunk_count > 1:
            print("✅ Direct vLLM streaming works!")
        else:
            print("❌ Direct vLLM not streaming properly")
            
    except Exception as e:
        print(f"❌ Direct vLLM test failed: {e}")


if __name__ == "__main__":
    asyncio.run(quick_stream_test())
    asyncio.run(test_direct_vllm()) 