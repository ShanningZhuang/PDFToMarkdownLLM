#!/usr/bin/env python3
"""
Comprehensive test for Chinese PDF encoding fix
"""

import asyncio
import httpx
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services import PDFConverterService, VLLMService


async def test_complete_chinese_workflow():
    """Test the complete workflow that would cause the original error"""
    print("🔍 Testing Complete Chinese PDF Workflow")
    print("=" * 60)
    
    # Step 1: Simulate problematic content from MarkItDown
    print("📋 Step 1: Simulating MarkItDown output with encoding issues")
    
    # This simulates what MarkItDown might output from a Chinese PDF
    # with mixed encodings that cause the latin-1 error
    problematic_markdown = (
        "# 中文文档标题\n\n"
        "这是从PDF提取的中文内容，可能包含编码问题。\n\n"
        "## 功能列表\n"
        "- 第一个功能项目\n"
        "- 第二个   功能   项目\n"  # Extra spaces that need cleaning
        "- 第三个功能项目\n\n"
        "正文内容包含    多余的    空格。\n\n"
        # Add some problematic characters that would cause latin-1 errors
        + chr(256) + chr(257) + chr(258) +  # Characters > 255
        "\n\n更多中文内容需要清理和格式化。"
    )
    
    print(f"   Raw content length: {len(problematic_markdown)} characters")
    print(f"   Contains problematic chars: {any(ord(c) > 255 for c in problematic_markdown)}")
    
    # Step 2: Test PDF service encoding fix
    print("\n📋 Step 2: Testing PDF service encoding fix")
    pdf_service = PDFConverterService()
    
    try:
        fixed_markdown = pdf_service._fix_encoding_issues(problematic_markdown, "test_chinese.pdf")
        fixed_markdown.encode('utf-8')  # This should not fail
        print("   ✅ PDF service encoding fix successful")
        print(f"   Fixed content length: {len(fixed_markdown)} characters")
    except Exception as e:
        print(f"   ❌ PDF service encoding fix failed: {e}")
        return
    
    # Step 3: Test vLLM service encoding verification
    print("\n📋 Step 3: Testing vLLM service encoding verification")
    vllm_service = VLLMService()
    
    try:
        # This should trigger the encoding verification in the streaming function
        verified_content = vllm_service._fix_encoding_issues(fixed_markdown, "streaming_input")
        verified_content.encode('utf-8')  # This should not fail
        print("   ✅ vLLM service encoding verification successful")
    except Exception as e:
        print(f"   ❌ vLLM service encoding verification failed: {e}")
        return
    
    # Step 4: Test the actual streaming API with this content
    print("\n📋 Step 4: Testing streaming API with fixed content")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            payload = {"markdown_content": verified_content}
            
            start_time = time.time()
            
            async with client.stream(
                "POST", 
                "http://localhost:8001/clean-markdown-stream",
                json=payload,
                headers={"Content-Type": "application/json; charset=utf-8"}
            ) as response:
                
                if response.status_code != 200:
                    error_content = await response.aread()
                    print(f"   ❌ API Error {response.status_code}: {error_content}")
                    return
                
                print(f"   📊 Status: {response.status_code}")
                
                chunks = []
                chunk_count = 0
                
                async for chunk in response.aiter_text():
                    if chunk:
                        chunk_count += 1
                        chunks.append(chunk)
                        
                        # Verify each chunk can be encoded (this was the original error)
                        try:
                            chunk.encode('utf-8')
                        except UnicodeEncodeError as e:
                            print(f"   ❌ Chunk {chunk_count} encoding error: {e}")
                            return
                        
                        if chunk_count <= 5:
                            print(f"   Chunk {chunk_count}: {repr(chunk[:30])}")
                
                total_time = time.time() - start_time
                full_response = ''.join(chunks)
                
                # Final verification
                try:
                    full_response.encode('utf-8')
                    print(f"\n   ✅ All {chunk_count} chunks processed successfully!")
                    print(f"   📊 Total time: {total_time:.3f}s")
                    print(f"   📊 Response length: {len(full_response)} characters")
                    print(f"   📊 Contains Chinese: {'✅' if any(ord(c) > 127 for c in full_response) else '❌'}")
                    
                    print(f"\n📄 Cleaned Chinese content:")
                    print("-" * 40)
                    print(full_response[:200] + "..." if len(full_response) > 200 else full_response)
                    print("-" * 40)
                    
                except UnicodeEncodeError as e:
                    print(f"   ❌ Final encoding verification failed: {e}")
                    
        except Exception as e:
            print(f"   ❌ Streaming API test failed: {e}")
            import traceback
            traceback.print_exc()


def test_edge_cases():
    """Test various edge cases that might occur"""
    print("\n🔍 Testing Edge Cases")
    print("=" * 40)
    
    service = PDFConverterService()
    
    edge_cases = [
        ("empty_string", ""),
        ("only_ascii", "Hello World"),
        ("only_chinese", "你好世界"),
        ("mixed_valid", "Hello 你好 World 世界"),
        ("null_chars", "Test\x00\x01\x02中文"),
        ("high_unicode", "Test" + chr(0x1F600) + "中文"),  # Emoji
    ]
    
    for case_name, content in edge_cases:
        try:
            fixed = service._fix_encoding_issues(content, f"{case_name}.pdf")
            fixed.encode('utf-8')
            print(f"   ✅ {case_name}: OK")
        except Exception as e:
            print(f"   ❌ {case_name}: {e}")


if __name__ == "__main__":
    test_edge_cases()
    asyncio.run(test_complete_chinese_workflow()) 