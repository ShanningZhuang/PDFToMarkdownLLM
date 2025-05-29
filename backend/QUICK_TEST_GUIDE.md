# Quick Test Guide

Fast reference for testing the PDF to Markdown converter backend with debugging.

## 🚀 Quick Start

```bash
# Install test dependencies
pip install -r test_requirements.txt

# Run all tests
python run_tests.py
```

## 🐛 Debug Failed Tests

### See Error Details Before Skips
```bash
# Run with debug output to see actual errors
python run_tests.py --debug

# Run specific test with full error details
python run_tests.py --file test_markdown_cleaning --function test_clean_markdown_debug_error --debug
```

### Analyze Token Limits
```bash
# Test different content sizes to find exact token limits
python run_tests.py --file test_markdown_cleaning --function test_clean_markdown_token_limit_analysis --debug
```

### Test Specific Issues
```bash
# Test PDF conversion only (no LLM)
python run_tests.py --file test_pdf_conversion --function test_convert_text_only --debug

# Test health checks
python run_tests.py --file test_health --debug

# Test vLLM management
python run_tests.py --file test_vllm_management --debug
```

## 📊 Common Test Commands

```bash
# Run tests with coverage
python run_tests.py --coverage

# Run fast tests only
python run_tests.py --fast

# Run specific test file
python run_tests.py --file test_health

# Run with HTML report
python run_tests.py --html

# Verbose output
python run_tests.py --verbose
```

## 🎯 Debugging Your Token Issue

Based on your question about seeing errors before skips, run these:

```bash
# 1. See the actual error details
python run_tests.py --file test_markdown_cleaning --function test_clean_markdown_debug_error --debug

# 2. Analyze different content sizes  
python run_tests.py --file test_markdown_cleaning --function test_clean_markdown_token_limit_analysis --debug

# 3. Test all markdown cleaning with full error output
python run_tests.py --file test_markdown_cleaning --debug
```

## 📋 Expected Output

### Before (old behavior):
```
SKIPPED - Token limit exceeded - expected for large content
```

### After (new debugging):
```
🚨 DEBUGGING INFO - Markdown Cleaning Failed:
Status Code: 500
Error Detail: Request to vLLM failed: 400 Client Error: Bad Request for url: http://localhost:8000/v1/chat/completions
Full Response: {
  "detail": "Request to vLLM failed: 400 Client Error: Bad Request"
}
Content Length: 523 characters
Content Preview: # Test Document...

❌ ERROR ANALYSIS:
Error Type: Internal Server Error
🎯 Diagnosis: Model Loading/Availability Issue
Suggested Fix: Check vLLM service status and model configuration
```

## 🔧 Prerequisites

- Backend running on `localhost:8001`
- Sample PDF file in parent directory (for PDF tests)
- vLLM service (tests skip gracefully if unavailable)

## 📚 Full Documentation

- Complete testing guide: `TESTING.md`
- API documentation: `API_DOCS.md`
- Backend documentation: `README.md` 