# PDF to Markdown Converter Backend

A FastAPI-based backend service that converts PDF documents to Markdown format using MarkItDown and cleans the content using a local vLLM deployment.

## Features

- 📄 PDF to Markdown conversion using MarkItDown
- 🤖 Content cleaning and enhancement using vLLM
- 🚀 Fast and async processing
- 🐳 Docker support
- 📊 Health checks and monitoring
- 🔒 File validation and security
- 📖 Comprehensive API documentation

## Quick Start

### Prerequisites

- Python 3.11+
- vLLM service running (typically on port 8000)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the server:
```bash
python main.py
```

Or use the startup script:
```bash
./start.sh
```

### Docker

Build and run with Docker:
```bash
docker build -t pdf2md-backend .
docker run -p 8001:8001 pdf2md-backend
```

## Configuration

Configure the service using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8001` | Server port |
| `VLLM_BASE_URL` | `http://localhost:8000` | vLLM service URL |
| `VLLM_MODEL_NAME` | `mistralai/Mistral-7B-Instruct-v0.3` | Model name |
| `MAX_FILE_SIZE_MB` | `50` | Maximum file size |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Check

```http
GET /health
```

Returns the health status of the API and vLLM service.

**Response:**
```json
{
  "api": "healthy",
  "vllm": "healthy"
}
```

### Upload PDF

```http
POST /upload
```

Upload a PDF file and convert it to Markdown.

**Parameters:**
- `file` (form-data): PDF file to upload
- `clean_with_llm` (query, optional): Whether to clean with vLLM (default: true)

**Response:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "raw_markdown": "# Document\n\nContent...",
  "cleaned_markdown": "# Document\n\nCleaned content...",
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

### Convert Text Only

```http
POST /convert-text
```

Convert PDF to Markdown without LLM cleaning (faster).

**Parameters:**
- `file` (form-data): PDF file to upload

### Clean Markdown

```http
POST /clean-markdown
```

Clean existing Markdown content using vLLM.

**Request Body:**
```json
{
  "markdown_content": "# Document\n\nContent with errors..."
}
```

**Response:**
```json
{
  "success": true,
  "original_content": "# Document\n\nContent with errors...",
  "cleaned_content": "# Document\n\nCleaned content...",
  "content_length": 1234
}
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Error Handling

The API returns standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid file, missing parameters)
- `422`: Unprocessable Entity (PDF conversion failed)
- `500`: Internal Server Error

Error responses include details:
```json
{
  "detail": "Error description"
}
```

## File Limits

- **File Size**: Maximum 50MB (configurable)
- **File Type**: Only PDF files are accepted
- **Content**: Must contain extractable text

## Development

### Project Structure

```
backend/
├── main.py           # FastAPI application
├── config.py         # Configuration management
├── services.py       # Business logic services
├── utils.py          # Utility functions
├── requirements.txt  # Python dependencies
├── Dockerfile        # Docker configuration
└── start.sh         # Startup script
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Monitoring

### Health Checks

The service provides health check endpoints for monitoring:

- `/` - Basic health check
- `/health` - Detailed health including vLLM connectivity

### Logging

The service logs important events:
- File uploads and processing
- vLLM interactions
- Errors and warnings

Configure log level with `LOG_LEVEL` environment variable.

## Security Considerations

- File type validation (PDF only)
- File size limits
- Filename sanitization
- Non-root Docker user
- CORS configuration

## Troubleshooting

### Common Issues

1. **vLLM Connection Failed**
   - Check if vLLM service is running
   - Verify `VLLM_BASE_URL` configuration
   - Check network connectivity

2. **PDF Conversion Failed**
   - Ensure PDF contains extractable text
   - Check file isn't corrupted
   - Verify file size limits

3. **Memory Issues**
   - Large PDFs may require more memory
   - Consider processing in chunks
   - Monitor system resources

### Logs

Check logs for detailed error information:
```bash
# Docker logs
docker logs <container-id>

# Local development
tail -f /var/log/pdf2md-backend.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details. 