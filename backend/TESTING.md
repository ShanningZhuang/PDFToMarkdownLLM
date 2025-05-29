# Testing Guide

This document describes the professional pytest-based testing approach for the PDF to Markdown converter backend.

## Overview

The testing suite has been completely redesigned to use **pytest** with a clean, professional structure that follows industry best practices.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py             # Pytest fixtures and configuration
├── test_health.py          # Health check and status tests
├── test_pdf_conversion.py  # PDF conversion functionality tests
├── test_markdown_cleaning.py # Markdown cleaning tests
├── test_vllm_management.py # vLLM service management tests
└── test_unit.py            # Unit tests (no server required)
```

## Key Features

### ✅ Professional Setup
- **pytest** as the testing framework
- **pytest-asyncio** for async test support
- **httpx** for HTTP client testing
- **pytest-cov** for coverage reporting
- **pytest-html** for HTML reports
- **pytest-xdist** for parallel testing

### ✅ Clean Architecture
- **Modular test files** organized by functionality
- **Reusable fixtures** in `conftest.py`
- **Async support** for API testing
- **Parameterized tests** for comprehensive coverage
- **Graceful error handling** for missing dependencies

### ✅ Easy to Use
- **Simple test runner** (`run_tests.py`) with multiple options
- **Clear test output** with timing and coverage
- **Flexible execution** (single files, parallel, coverage, etc.)
- **No messy scripts** or complex setup

## Quick Start

### 1. Install Dependencies
```bash
pip install -r test_requirements.txt
```

### 2. Run Tests
```bash
# Basic test run
pytest

# Or use the test runner
python run_tests.py
```

### 3. Advanced Options
```bash
# Run with coverage
python run_tests.py --coverage

# Run specific test file
python run_tests.py --file test_health

# Run in parallel
python run_tests.py --parallel

# Generate HTML report
python run_tests.py --html

# Verbose output
python run_tests.py --verbose
```

## Test Categories

### 🏥 Health Tests (`test_health.py`)
- API health check endpoint
- vLLM service status
- Response time validation

### 📄 PDF Conversion Tests (`test_pdf_conversion.py`)
- PDF upload with/without LLM cleaning
- File validation and error handling
- Performance testing
- Invalid file handling

### 🧹 Markdown Cleaning Tests (`test_markdown_cleaning.py`)
- Content cleaning functionality
- Token limit handling
- Error scenarios
- Input validation

### ⚙️ vLLM Management Tests (`test_vllm_management.py`)
- Service start/stop/restart
- Status monitoring
- Error handling
- Process management

### 🔧 Unit Tests (`test_unit.py`)
- Project structure validation
- Fixture testing
- No server dependencies

## Test Configuration

### `pytest.ini`
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
    --durations=10
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

### Fixtures (`conftest.py`)
- **`client`**: Async HTTP client for API testing
- **`base_url`**: Configurable API base URL
- **`sample_pdf_path`**: Automatic PDF file detection
- **`sample_markdown`**: Sample content for testing

## Test Runner (`run_tests.py`)

Professional test runner with multiple options:

```bash
# Install dependencies and run tests
python run_tests.py --install-deps

# Run with coverage and HTML report
python run_tests.py --coverage --html

# Run specific test file with verbose output
python run_tests.py --file test_health --verbose

# Run only fast tests in parallel
python run_tests.py --fast --parallel
```

### Available Options
- `--coverage`: Generate coverage report
- `--html`: Generate HTML test report
- `--parallel`: Run tests in parallel
- `--verbose`: Verbose output
- `--fast`: Skip slow tests
- `--file`: Run specific test file
- `--install-deps`: Install test dependencies

## Sample Output

```bash
$ python run_tests.py --verbose
========================= test session starts =========================
tests/test_health.py::test_health_check PASSED           [ 12%]
tests/test_health.py::test_vllm_status PASSED            [ 25%]
tests/test_pdf_conversion.py::test_pdf_upload_with_llm PASSED [ 37%]
tests/test_pdf_conversion.py::test_pdf_upload_without_llm PASSED [ 50%]
tests/test_pdf_conversion.py::test_convert_text_only PASSED [ 62%]
tests/test_markdown_cleaning.py::test_clean_markdown_small_content PASSED [ 75%]
tests/test_vllm_management.py::test_vllm_status_after_operations PASSED [ 87%]
========================= 22 passed, 6 skipped in 15.23s =========================
```

## Testing Best Practices

### ✅ What We Improved
1. **Removed messy multi-method scripts** - Clean, focused test files
2. **Professional pytest setup** - Industry standard testing framework
3. **Async support** - Proper async/await testing with httpx
4. **Modular structure** - Each test file has a specific purpose
5. **Reusable fixtures** - DRY principle with shared test components
6. **Error handling** - Graceful handling of missing dependencies
7. **Performance testing** - Response time validation and benchmarking
8. **Easy execution** - Simple commands for different testing scenarios

### ✅ Key Benefits
- **Maintainable**: Clear structure and separation of concerns
- **Scalable**: Easy to add new tests and test categories
- **Professional**: Follows pytest best practices and conventions
- **Flexible**: Multiple execution options and configurations
- **Reliable**: Proper async handling and error management
- **Fast**: Parallel execution and selective test running

## Prerequisites for Full Testing

- **Running Server**: Integration tests expect backend on `localhost:8001`
- **Sample PDF**: Place a PDF file (like `AlexNet.pdf`) in parent directory
- **vLLM Service**: Some tests require vLLM (gracefully skip if unavailable)

## Coverage Reporting

Generate detailed coverage reports:

```bash
# Terminal coverage report
python run_tests.py --coverage

# HTML coverage report
python run_tests.py --coverage --html
# View: htmlcov/index.html
```

## Continuous Integration

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r test_requirements.txt
    python run_tests.py --coverage
```

## Migration from Old Testing

The old testing approach with multiple methods and messy scripts has been completely replaced with this clean, professional pytest-based system. The new approach provides:

- **Better organization** with focused test files
- **Professional tooling** with pytest ecosystem
- **Easier maintenance** with clear structure
- **Better reporting** with coverage and HTML reports
- **Simpler execution** with the test runner script

This testing approach follows industry best practices and provides a solid foundation for maintaining and extending the test suite. 