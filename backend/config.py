import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8001
    
    # vLLM Service Configuration
    vllm_base_url: str = "http://localhost:8000"
    vllm_model_name: str = "Qwen/Qwen3-8B"
    vllm_auto_start: bool = True  # Auto-start vLLM service
    vllm_startup_timeout: int = 300  # Timeout for vLLM startup (seconds)
    vllm_gpu_memory_utilization: float = 0.8
    vllm_max_model_len: int = 32768
    
    # File Upload Configuration
    max_file_size_mb: int = 50
    
    # CORS Configuration
    allowed_origins: List[str] = ["*"]  # In production, specify actual domains
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # vLLM Parameters
    vllm_max_tokens: int = 16384
    vllm_temperature: float = 0.1
    vllm_timeout: int = 300  # seconds
    
    # Streaming Configuration
    vllm_stream_chunk_size: int = 1  # Size of streaming chunks
    vllm_disable_log_stats: bool = True  # Disable vLLM stats logging for better streaming
    
    # Model Download Configuration
    model_cache_dir: str = "./models"  # Directory to cache downloaded models
    auto_download_model: bool = True  # Auto-download model if not found
    
    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False


# Global settings instance
settings = Settings() 