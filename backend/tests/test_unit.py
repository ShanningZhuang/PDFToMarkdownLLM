"""
Unit tests that don't require the server to be running
"""

import pytest
from pathlib import Path


def test_pytest_setup():
    """Test that pytest is working correctly."""
    assert True


def test_project_structure():
    """Test that the project has the expected structure."""
    # Check that main files exist
    assert Path("main.py").exists()
    assert Path("config.py").exists()
    assert Path("services.py").exists()
    assert Path("requirements.txt").exists()


def test_test_structure():
    """Test that the test structure is correct."""
    # Check test directory structure
    assert Path("tests").exists()
    assert Path("tests/__init__.py").exists()
    assert Path("tests/conftest.py").exists()
    assert Path("pytest.ini").exists()


@pytest.mark.parametrize("test_file", [
    "test_health.py",
    "test_pdf_conversion.py", 
    "test_markdown_cleaning.py",
    "test_vllm_management.py"
])
def test_test_files_exist(test_file):
    """Test that all expected test files exist."""
    assert Path(f"tests/{test_file}").exists()


def test_sample_markdown_fixture(sample_markdown):
    """Test that the sample markdown fixture works."""
    assert isinstance(sample_markdown, str)
    assert len(sample_markdown) > 0
    assert "# Test Document" in sample_markdown


def test_base_url_fixture(base_url):
    """Test that the base URL fixture works."""
    assert isinstance(base_url, str)
    assert base_url == "http://localhost:8001" 