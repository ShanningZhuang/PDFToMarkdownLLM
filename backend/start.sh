#!/bin/bash

# Backend startup script for PDF to Markdown converter

echo "Starting PDF to Markdown Converter Backend..."

# Set default environment variables if not set
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-8001}
export VLLM_BASE_URL=${VLLM_BASE_URL:-"http://localhost:8000"}
export VLLM_MODEL_NAME=${VLLM_MODEL_NAME:-"mistralai/Mistral-7B-Instruct-v0.3"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

echo "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  vLLM URL: $VLLM_BASE_URL"
echo "  vLLM Model: $VLLM_MODEL_NAME"
echo "  Log Level: $LOG_LEVEL"

# Check if running in development mode
if [ "$DEVELOPMENT" = "true" ]; then
    echo "Running in development mode with auto-reload..."
    uvicorn main:app --host $HOST --port $PORT --reload --log-level info
else
    echo "Running in production mode..."
    uvicorn main:app --host $HOST --port $PORT --workers 4 --log-level info
fi 