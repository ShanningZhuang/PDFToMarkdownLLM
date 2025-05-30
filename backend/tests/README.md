# Test Suite Documentation

This directory contains comprehensive pytest tests for the PDF to Markdown converter backend.

## Test Structure

### Core Test Files

#### `test_encoding.py`
Tests for encoding functionality including Chinese character support:
- **TestFilenameEncoding**: HTTP header filename encoding (latin-1 compatibility)
- **TestPDFEncodingFix**: PDF content encoding fixes for MarkItDown issues
- **TestVLLMEncodingVerification**: vLLM service encoding verification
- **TestStreamingEncoding**: Encoding safety in streaming context
- **TestEndToEndEncoding**: Complete encoding workflow tests
- **TestEdgeCases**: Unicode edge cases and error conditions

#### `test_streaming.py`
Tests for streaming functionality including token-by-token streaming:
- **TestStreamingGenerators**: Sync vs async generator behavior
- **TestVLLMStreamingService**: vLLM streaming service functionality
- **TestStreamingEndpoints**: API endpoint streaming tests
- **TestStreamingPerformance**: Latency and memory efficiency tests
- **TestStreamingErrorHandling**: Error recovery in streaming
- **TestStreamingIntegration**: Integration scenarios

#### `test_api_endpoints.py`
Tests for all API endpoints:
- **TestHealthEndpoints**: Health check and status endpoints
- **TestVLLMControlEndpoints**: vLLM start/stop/restart controls
- **TestUploadEndpoints**: PDF upload functionality
- **TestMarkdownCleaningEndpoints**: Markdown cleaning endpoints
- **TestFilenameEncoding**: Filename encoding utilities
- **TestErrorHandling**: Error handling across endpoints
- **TestCORSAndHeaders**: CORS and HTTP header tests
- **TestRequestValidation**: Input validation tests
- **TestIntegrationScenarios**: End-to-end workflows

### Existing Test Files

#### `test_pdf_conversion.py`
Tests for PDF conversion functionality using MarkItDown.

#### `test_markdown_cleaning.py`
Tests for markdown cleaning with vLLM.

#### `test_vllm_management.py`
Tests for vLLM service management.

#### `test_health.py`
Tests for health check functionality.

#### `test_unit.py`
Basic unit tests.

## Running Tests

### Run All Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Run Specific Test Files
```bash
# Encoding tests
python -m pytest tests/test_encoding.py -v

# Streaming tests
python -m pytest tests/test_streaming.py -v

# API endpoint tests
python -m pytest tests/test_api_endpoints.py -v
```

### Run Tests with Coverage
```bash
python -m pytest tests/ --cov=. --cov-report=html
```

### Run Tests with Specific Markers
```bash
# Run only integration tests
python -m pytest tests/ -m integration -v

# Run only unit tests
python -m pytest tests/ -m "not integration" -v
```

## Test Categories

### Unit Tests
- Individual function testing
- Mocked dependencies
- Fast execution
- No external services required

### Integration Tests
- End-to-end workflows
- Real service interactions
- Slower execution
- May require running services

### Performance Tests
- Streaming latency tests
- Memory efficiency tests
- Load testing scenarios

## Key Test Features

### Comprehensive Coverage
- ✅ All encoding scenarios (ASCII, Chinese, mixed)
- ✅ Streaming vs buffering behavior
- ✅ Error handling and edge cases
- ✅ API endpoint validation
- ✅ File upload scenarios
- ✅ vLLM service management

### Realistic Scenarios
- Chinese PDF files with Chinese filenames
- Large file uploads
- Network errors and timeouts
- Invalid input handling
- Service unavailability

### Performance Validation
- Token-by-token streaming verification
- Memory usage patterns
- Response time measurements
- Concurrent request handling

## Test Configuration

### pytest.ini
Configuration file with:
- Test discovery patterns
- Async test settings
- Warning filters
- Output formatting

### conftest.py
Shared fixtures and configuration:
- Mock services
- Test data setup
- Common utilities

## Debugging Tests

### Verbose Output
```bash
python -m pytest tests/ -v -s
```

### Stop on First Failure
```bash
python -m pytest tests/ -x
```

### Run Specific Test
```bash
python -m pytest tests/test_encoding.py::TestFilenameEncoding::test_chinese_filename_url_encoded -v
```

### Debug Mode
```bash
python -m pytest tests/ --pdb
```

## Test Data

Tests use:
- Mock PDF content for upload tests
- Sample Chinese text for encoding tests
- Simulated vLLM responses for streaming tests
- Realistic error scenarios

## Continuous Integration

Tests are designed to:
- Run without external dependencies (when mocked)
- Provide clear failure messages
- Execute quickly for CI/CD pipelines
- Cover all critical functionality

## Adding New Tests

When adding new functionality:
1. Add unit tests for individual functions
2. Add integration tests for workflows
3. Add error handling tests
4. Update this documentation
5. Ensure tests are deterministic and fast 