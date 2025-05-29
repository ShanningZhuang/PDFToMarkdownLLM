"""
Pytest configuration and shared fixtures for PDF to Markdown converter tests
"""

import pytest
import pytest_asyncio
import asyncio
import httpx
from pathlib import Path
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def base_url() -> str:
    """Base URL for the API server."""
    return "http://localhost:8001"


@pytest_asyncio.fixture
async def client(base_url: str) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for API testing."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
def sample_pdf_path() -> str:
    """Path to a sample PDF file for testing."""
    # Look for PDF files in the parent directory or test data
    test_files = [
        "../logs/AlexNet.pdf",
        "test_data/sample.pdf",
        "sample.pdf"
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            return file_path
    
    # If no PDF found, skip tests that require it
    pytest.skip("No sample PDF file found for testing")


@pytest.fixture
def sample_markdown() -> str:
    """Sample markdown content for testing."""
    return """
# Test Document

This is a **test document** with some *formatting*.

## Section 1

- Item 1
- Item 2
- Item 3

## Section 2

Here's some code:

```python
def hello_world():
    print("Hello, World!")
```

And a table:

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
| Value 3  | Value 4  |
""" 