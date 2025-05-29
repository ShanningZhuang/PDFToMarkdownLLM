#!/bin/bash

# Backend startup script for PDF to Markdown converter

echo "Starting PDF to Markdown Converter Backend..."

# Set default environment variables if not set
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-8001}
export VLLM_BASE_URL=${VLLM_BASE_URL:-"http://localhost:8000"}
export VLLM_MODEL_NAME=${VLLM_MODEL_NAME:-"mistralai/Mistral-7B-Instruct-v0.3"}
export VLLM_AUTO_START=${VLLM_AUTO_START:-"true"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}
export MODEL_CACHE_DIR=${MODEL_CACHE_DIR:-"./models"}
export MAX_FILE_SIZE_MB=${MAX_FILE_SIZE_MB:-50}

# Create model cache directory
mkdir -p "$MODEL_CACHE_DIR"

echo "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  vLLM URL: $VLLM_BASE_URL"
echo "  vLLM Model: $VLLM_MODEL_NAME"
echo "  vLLM Auto-start: $VLLM_AUTO_START"
echo "  Log Level: $LOG_LEVEL"
echo "  Model Cache: $MODEL_CACHE_DIR"
echo "  Max File Size: ${MAX_FILE_SIZE_MB}MB"

# Check for GPU availability
if command -v nvidia-smi &> /dev/null; then
    echo "GPU Status:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits 2>/dev/null || echo "  Could not query GPU status"
else
    echo "  No NVIDIA GPU detected (will use CPU mode)"
fi

# Set environment variables for model caching
export TRANSFORMERS_CACHE="$MODEL_CACHE_DIR"
export HF_HOME="$MODEL_CACHE_DIR"

# Check if running in development mode
if [ "$DEVELOPMENT" = "true" ]; then
    echo "Running in development mode with auto-reload..."
    uvicorn main:app --host $HOST --port $PORT --reload --log-level info
else
    echo "Running in production mode..."
    # In production, use more workers but start with 1 for vLLM compatibility
    uvicorn main:app --host $HOST --port $PORT --workers 1 --log-level info
fi 