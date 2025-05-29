#!/usr/bin/env python3
"""
Test Chinese character encoding in streaming endpoints
"""

import asyncio
import httpx
import time


async def test_chinese_markdown_stream():
    """Test streaming with Chinese markdown content"""
    print("🔍 Testing Chinese Markdown Streaming")
    print("=" * 50)
    
    # Chinese markdown content
    chinese_content = """# 测试文档

这是一个中文测试文档。

## 功能列表
- 第一项功能
- 第二项   功能
- 第三项功能

这个文档需要清理   和   格式化。

**重要**: 保持中文内容不变。
"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            payload = {"markdown_content": chinese_content}
            print(f"📤 Testing with Chinese content ({len(chinese_content)} chars)")
            print(f"Original content:\n{chinese_content}\n")
            
            start_time = time.time()
            
            async with client.stream(
                "POST", 
                "http://localhost:8001/clean-markdown-stream",
                json=payload,
                headers={"Content-Type": "application/json; charset=utf-8"}
            ) as response:
                
                if response.status_code != 200:
                    error_content = await response.aread()
                    print(f"❌ Error {response.status_code}: {error_content}")
                    return
                
                print(f"📊 Status: {response.status_code}")
                print(f"📊 Response Headers:")
                for key, value in response.headers.items():
                    if 'content' in key.lower() or 'encoding' in key.lower():
                        print(f"   {key}: {value}")
                
                print("\n🔄 Streaming Chinese response:")
                print("-" * 30)
                
                chunks = []
                chunk_count = 0
                
                async for chunk in response.aiter_text():
                    if chunk:
                        chunk_count += 1
                        chunks.append(chunk)
                        elapsed = time.time() - start_time
                        
                        # Show first few chunks to verify encoding
                        if chunk_count <= 10:
                            print(f"[{elapsed:.3f}s] Chunk {chunk_count}: {repr(chunk)}")
                        elif chunk_count % 10 == 0:
                            print(f"[{elapsed:.3f}s] ... chunk {chunk_count}")
                
                total_time = time.time() - start_time
                full_response = ''.join(chunks)
                
                print("-" * 30)
                print(f"\n📊 Summary:")
                print(f"   Total chunks: {chunk_count}")
                print(f"   Total time: {total_time:.3f}s")
                print(f"   Response length: {len(full_response)} characters")
                print(f"   Contains Chinese: {'✅' if any(ord(c) > 127 for c in full_response) else '❌'}")
                
                print(f"\n🔄 Final cleaned content:")
                print(full_response)
                
                if chunk_count > 1:
                    print("\n✅ STREAMING WORKS with Chinese content!")
                else:
                    print("\n❌ NOT STREAMING - Only one chunk received")
                
        except Exception as e:
            print(f"❌ Chinese streaming test failed: {e}")
            import traceback
            traceback.print_exc()


async def test_chinese_json_metadata():
    """Test JSON metadata with Chinese filename"""
    print("\n🔍 Testing Chinese Filename in JSON Metadata")
    print("=" * 50)
    
    # Test the JSON encoding directly
    import json
    
    test_metadata = {
        "filename": "测试文档.pdf",
        "file_size_bytes": 12345,
        "raw_content_length": 678
    }
    
    try:
        # Test JSON serialization with Chinese characters
        metadata_json = json.dumps(test_metadata, ensure_ascii=False)
        print(f"✅ JSON serialization successful:")
        print(f"   {metadata_json}")
        
        # Test if it can be parsed back
        parsed = json.loads(metadata_json)
        print(f"✅ JSON parsing successful:")
        print(f"   filename: {parsed['filename']}")
        
        # Test encoding/decoding
        encoded = metadata_json.encode('utf-8')
        decoded = encoded.decode('utf-8')
        print(f"✅ UTF-8 encoding/decoding successful")
        
    except Exception as e:
        print(f"❌ JSON metadata test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_chinese_json_metadata())
    asyncio.run(test_chinese_markdown_stream()) 