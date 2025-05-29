# API Documentation

Complete API reference for the PDF to Markdown Converter Backend.

## Base URL

```
http://localhost:8001
```

## Authentication

No authentication required for local development.

---

## Health Check Endpoints

### GET `/`

Basic health check endpoint.

**Response:**
```json
{
  "message": "PDF to Markdown Converter API is running"
}
```

### GET `/health`

Detailed health check including vLLM connectivity.

**Response:**
```json
{
  "api": "healthy",
  "vllm": "healthy",
  "vllm_process": {
    "process_running": true,
    "process_pid": 12345,
    "port": 8000,
    "model": "mistralai/Mistral-7B-Instruct-v0.3",
    "memory_usage_mb": 2048.5,
    "gpu_available": true,
    "service_responsive": true
  }
}
```

**Fields:**
- `api`: Always "healthy" if API is running
- `vllm`: "healthy", "unhealthy", or "error: {message}"
- `vllm_process`: Detailed process information from vLLM manager

---

## vLLM Management Endpoints

### GET `/vllm/status`

Get detailed vLLM service status.

**Response:**
```json
{
  "process_running": true,
  "process_pid": 12345,
  "port": 8000,
  "model": "mistralai/Mistral-7B-Instruct-v0.3",
  "memory_usage_mb": 2048.5,
  "gpu_available": true,
  "service_responsive": true
}
```

### POST `/vllm/start`

Start vLLM service.

**Request Body (Optional):**
```json
{
  "model_name": "mistralai/Mistral-7B-Instruct-v0.3"
}
```

**Response:**
```json
{
  "success": true,
  "message": "vLLM service started successfully",
  "status": {
    "process_running": true,
    "process_pid": 12345,
    "port": 8000,
    "model": "mistralai/Mistral-7B-Instruct-v0.3",
    "memory_usage_mb": 2048.5,
    "gpu_available": true
  }
}
```

### POST `/vllm/stop`

Stop vLLM service.

**Response:**
```json
{
  "success": true,
  "message": "vLLM service stopped successfully"
}
```

### POST `/vllm/restart`

Restart vLLM service.

**Request Body (Optional):**
```json
{
  "model_name": "mistralai/Mistral-7B-Instruct-v0.3"
}
```

**Response:**
```json
{
  "success": true,
  "message": "vLLM service restarted successfully",
  "status": {
    "process_running": true,
    "process_pid": 12345,
    "port": 8000,
    "model": "mistralai/Mistral-7B-Instruct-v0.3",
    "memory_usage_mb": 2048.5,
    "gpu_available": true
  }
}
```

---

## PDF Processing Endpoints

### POST `/upload`

Upload PDF file and convert to markdown format.

**Request:**
- Content-Type: `multipart/form-data`
- Form field: `file` (PDF file)
- Query parameter: `clean_with_llm` (boolean, default: true)

**Example:**
```bash
curl -X POST "http://localhost:8001/upload?clean_with_llm=true" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "raw_markdown": "# Document Title\n\nRaw content from PDF...",
  "cleaned_markdown": "# Document Title\n\nCleaned content...",
  "cleaned_with_llm": true,
  "content_length": 1234,
  "metadata": {
    "original_filename": "document.pdf",
    "file_size_bytes": 102400,
    "conversion_method": "MarkItDown",
    "llm_cleaning": true
  }
}
```

**Fields:**
- `success`: Always true for successful requests
- `filename`: Original filename
- `raw_markdown`: Converted markdown before LLM cleaning
- `cleaned_markdown`: Final markdown content (may equal raw_markdown if cleaning failed or disabled)
- `cleaned_with_llm`: Boolean indicating if LLM cleaning was successful
- `content_length`: Length of final markdown content
- `metadata`: Additional processing information

**Error Responses:**

File validation error (400):
```json
{
  "detail": "Only PDF files are supported"
}
```

File size error (400):
```json
{
  "detail": "File size too large. Maximum size is 50MB"
}
```

vLLM service unavailable (503):
```json
{
  "detail": "vLLM service is not available and failed to start. Try again or use convert-text endpoint."
}
```

Processing error (500):
```json
{
  "detail": "Internal server error: {error_message}"
}
```

### POST `/convert-text`

Convert PDF to markdown without LLM cleaning (faster option).

**Request:**
- Content-Type: `multipart/form-data`
- Form field: `file` (PDF file)

**Response:**
Same as `/upload` endpoint but with `clean_with_llm: false` and `cleaned_markdown` equals `raw_markdown`.

```json
{
  "success": true,
  "filename": "document.pdf",
  "raw_markdown": "# Document Title\n\nContent from PDF...",
  "cleaned_markdown": "# Document Title\n\nContent from PDF...",
  "cleaned_with_llm": false,
  "content_length": 1234,
  "metadata": {
    "original_filename": "document.pdf",
    "file_size_bytes": 102400,
    "conversion_method": "MarkItDown",
    "llm_cleaning": false
  }
}
```

---

## Markdown Cleaning Endpoints

### POST `/clean-markdown`

Clean existing markdown content using vLLM.

**Request:**
```json
{
  "markdown_content": "# Document\n\nContent with errors and poor formatting..."
}
```

**Response:**
```json
{
  "success": true,
  "original_content": "# Document\n\nContent with errors and poor formatting...",
  "cleaned_content": "# Document\n\nCleaned and improved content...",
  "content_length": 567
}
```

**Fields:**
- `success`: Always true for successful requests
- `original_content`: Input markdown content
- `cleaned_content`: LLM-cleaned markdown content
- `content_length`: Length of cleaned content

**Error Responses:**

Empty content (400):
```json
{
  "detail": "Markdown content cannot be empty"
}
```

vLLM service unavailable (503):
```json
{
  "detail": "vLLM service is not available and failed to start"
}
```

Processing error (500):
```json
{
  "detail": "Failed to clean markdown: {error_message}"
}
```

### POST `/clean-markdown-stream`

Clean existing markdown content using vLLM with streaming response (token by token).

**Request:**
```json
{
  "markdown_content": "# Document\n\nContent with errors and poor formatting..."
}
```

**Response:**
- Content-Type: `text/plain`
- Headers: 
  - `X-Content-Type: streaming`
  - `Cache-Control: no-cache`
  - `Connection: keep-alive`

**Response Body:** Streaming text (cleaned markdown content token by token)

**Example with cURL:**
```bash
curl -X POST "http://localhost:8001/clean-markdown-stream" \
  -H "Content-Type: application/json" \
  -d '{"markdown_content": "# Test\n\nSample content..."}' \
  --no-buffer
```

**Example with Python:**
```python
import httpx

async with httpx.AsyncClient() as client:
    payload = {"markdown_content": "# Test\n\nContent..."}
    async with client.stream("POST", "/clean-markdown-stream", json=payload) as response:
        async for chunk in response.aiter_text():
            print(chunk, end="", flush=True)
```

**Error Responses:** Same as `/clean-markdown` endpoint.

### POST `/upload-stream`

Upload PDF file, convert to markdown, and clean with streaming LLM response.

**Request:**
- Content-Type: `multipart/form-data`
- Form field: `file` (PDF file)

**Response:**
- Content-Type: `text/plain`
- Headers:
  - `X-Content-Type: streaming`
  - `X-Filename: {original_filename}`
  - `Cache-Control: no-cache`
  - `Connection: keep-alive`

**Response Body:**
1. First chunk: JSON metadata (`data: {metadata}\n\n`)
2. Following chunks: Cleaned markdown content (token by token)

**Metadata Format:**
```json
{
  "filename": "document.pdf",
  "file_size_bytes": 102400,
  "raw_content_length": 5000
}
```

**Example with cURL:**
```bash
curl -X POST "http://localhost:8001/upload-stream" \
  -F "file=@document.pdf" \
  --no-buffer
```

**Example with Python:**
```python
import httpx

async with httpx.AsyncClient() as client:
    files = {'file': ('document.pdf', open('document.pdf', 'rb'), 'application/pdf')}
    async with client.stream("POST", "/upload-stream", files=files) as response:
        async for chunk in response.aiter_text():
            print(chunk, end="", flush=True)
```

**Error Responses:** Same as `/upload` endpoint.

---

## Streaming vs Non-Streaming

### When to Use Streaming

**Use Streaming When:**
- You want immediate feedback (see tokens as they're generated)
- Processing large documents (better user experience)
- Building interactive applications (like ChatGPT)
- You need to show progress to users

**Use Non-Streaming When:**
- You need the complete response for further processing
- You're building batch processing systems
- You prefer simpler response handling
- You need the response metadata (success flags, content length, etc.)

### Performance Comparison

| Aspect | Streaming | Non-Streaming |
|--------|-----------|---------------|
| **Time to first token** | ~0.1-0.5s | N/A (wait for complete response) |
| **Total processing time** | Same | Same |
| **User experience** | Interactive | Wait then complete |
| **Response format** | Text stream | JSON with metadata |
| **Error handling** | HTTP status + stream errors | JSON error format |

---

## Response Patterns

### Success Responses

All successful responses use HTTP status code `200` and include appropriate JSON data.

### Error Responses

Error responses use standard HTTP status codes:

- `400 Bad Request`: Client errors (invalid file, missing parameters)
- `422 Unprocessable Entity`: Validation errors
- `503 Service Unavailable`: vLLM service not available
- `500 Internal Server Error`: Unexpected server errors

Error response format:
```json
{
  "detail": "Error description"
}
```

---

## File Upload Constraints

- **File Type**: Only PDF files (`.pdf` extension)
- **File Size**: Maximum 50MB (configurable via `MAX_FILE_SIZE_MB`)
- **Content**: PDF must contain extractable text

---

## Configuration

The API behavior can be modified using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `VLLM_AUTO_START` | `true` | Auto-start vLLM service |
| `MAX_FILE_SIZE_MB` | `50` | Maximum file size |
| `VLLM_BASE_URL` | `http://localhost:8000` | vLLM service URL |
| `VLLM_MODEL_NAME` | `mistralai/Mistral-7B-Instruct-v0.3` | Model name |

---

## Interactive Documentation

When the server is running, visit:
- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc` 