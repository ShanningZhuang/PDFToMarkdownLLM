#!/usr/bin/env python3
"""
Test encoding fix for MarkItDown PDF conversion issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services import PDFConverterService


def test_encoding_fix():
    """Test the encoding fix function with problematic content"""
    print("🔍 Testing Encoding Fix Function")
    print("=" * 50)
    
    service = PDFConverterService()
    
    # Test cases that might come from MarkItDown with Chinese PDFs
    test_cases = [
        # Case 1: Normal Chinese content (should pass through unchanged)
        ("normal_chinese", "# 测试文档\n\n这是正常的中文内容。"),
        
        # Case 2: Mixed encoding content (common MarkItDown issue)
        ("mixed_encoding", "# Test\n\nSome text with ñáéíóú characters"),
        
        # Case 3: Content with latin-1 characters that can't be encoded to UTF-8 directly
        ("latin1_chars", "Test with special chars: " + chr(170) + chr(186) + chr(191)),
        
        # Case 4: Bytes instead of string
        ("bytes_content", "# 测试\n\n中文内容".encode('utf-8')),
        
        # Case 5: Problematic characters that cause UnicodeEncodeError
        ("problematic", "Test" + chr(128) + chr(255) + "中文"),
    ]
    
    for case_name, test_content in test_cases:
        print(f"\n📤 Testing case: {case_name}")
        print(f"   Input type: {type(test_content)}")
        print(f"   Input repr: {repr(test_content[:50])}")
        
        try:
            # Test our encoding fix
            fixed_content = service._fix_encoding_issues(test_content, f"test_{case_name}.pdf")
            
            # Verify the result can be encoded to UTF-8
            fixed_content.encode('utf-8')
            
            print(f"   ✅ Fixed successfully")
            print(f"   Output type: {type(fixed_content)}")
            print(f"   Output length: {len(fixed_content)} chars")
            print(f"   Contains Chinese: {'✅' if any(ord(c) > 127 for c in fixed_content) else '❌'}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")


def test_problematic_content_simulation():
    """Simulate the exact problematic content that might cause the latin-1 error"""
    print("\n🔍 Testing Problematic Content Simulation")
    print("=" * 50)
    
    # Simulate content that MarkItDown might extract from a Chinese PDF
    # This represents content with mixed encodings or characters outside ASCII range
    
    # Create problematic content that would cause 'latin-1' codec error
    problematic_chars = []
    for i in range(256, 270):  # Characters outside latin-1 range
        problematic_chars.append(chr(i))
    
    problematic_content = "# 文档标题\n\n这是中文内容" + "".join(problematic_chars) + "更多中文"
    
    print(f"📤 Created problematic content with {len(problematic_content)} characters")
    print(f"   Contains chars > 255: {any(ord(c) > 255 for c in problematic_content)}")
    
    service = PDFConverterService()
    
    try:
        # This should trigger our encoding fix
        fixed = service._fix_encoding_issues(problematic_content, "problematic.pdf")
        
        # Verify it can be used in streaming
        fixed.encode('utf-8')
        print("✅ Problematic content fixed successfully!")
        print(f"   Fixed length: {len(fixed)} characters")
        
        # Test if it can be used in the streaming context
        try:
            # Simulate what happens in the streaming function
            for i, chunk in enumerate(fixed[:10]):  # Test first 10 characters
                chunk.encode('utf-8')  # This should not fail
            print("✅ Fixed content works in streaming context!")
            
        except Exception as streaming_error:
            print(f"❌ Fixed content still fails in streaming: {streaming_error}")
            
    except Exception as e:
        print(f"❌ Encoding fix failed: {e}")


if __name__ == "__main__":
    test_encoding_fix()
    test_problematic_content_simulation() 