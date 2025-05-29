import asyncio
import logging
import os
import signal
import subprocess
import time
import psutil
from typing import Optional
import httpx

from config import settings

logger = logging.getLogger(__name__)


class VLLMManager:
    """Manager for vLLM service lifecycle"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.vllm_port = self._extract_port_from_url(settings.vllm_base_url)
        self.startup_timeout = settings.vllm_startup_timeout
        self.health_check_interval = 5  # seconds
        
    def _extract_port_from_url(self, url: str) -> int:
        """Extract port from vLLM base URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.port or 8000
        except Exception:
            return 8000
    
    async def start_vllm_service(self, model_name: Optional[str] = None) -> bool:
        """
        Start vLLM service if not already running
        
        Args:
            model_name: Model to load (defaults to settings.vllm_model_name)
            
        Returns:
            True if started successfully or already running
        """
        model_name = model_name or settings.vllm_model_name
        
        # Check if vLLM is already running
        if await self._is_vllm_running():
            logger.info("vLLM service is already running")
            return True
        
        # Check if port is available
        if self._is_port_in_use(self.vllm_port):
            logger.error(f"Port {self.vllm_port} is already in use")
            return False
        
        logger.info(f"Starting vLLM service with model: {model_name}")
        
        # Create model cache directory if it doesn't exist
        os.makedirs(settings.model_cache_dir, exist_ok=True)
        
        try:
            # Prepare vLLM command
            cmd = self._build_vllm_command(model_name)
            logger.info(f"vLLM command: {' '.join(cmd)}")
            
            # Prepare environment
            env = os.environ.copy()
            env.update({
                'TRANSFORMERS_CACHE': settings.model_cache_dir,
                'HF_HOME': settings.model_cache_dir,
                'CUDA_VISIBLE_DEVICES': '0' if self._has_gpu() else '',
            })
            
            # Start vLLM process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                preexec_fn=os.setsid  # Create new process group for clean shutdown
            )
            
            logger.info(f"vLLM process started with PID: {self.process.pid}")
            
            # Wait for vLLM to be ready
            if await self._wait_for_vllm_ready():
                logger.info("vLLM service started successfully")
                return True
            else:
                logger.error("vLLM service failed to start within timeout")
                await self.stop_vllm_service()
                return False
                
        except Exception as e:
            logger.error(f"Failed to start vLLM service: {e}")
            return False
    
    def _build_vllm_command(self, model_name: str) -> list[str]:
        """Build vLLM startup command"""
        cmd = [
            "python", "-m", "vllm.entrypoints.openai.api_server",
            "--model", model_name,
            "--host", "0.0.0.0",
            "--port", str(self.vllm_port),
            "--served-model-name", model_name,
            "--max-model-len", str(settings.vllm_max_model_len),
            "--disable-log-requests",
            "--trust-remote-code"
        ]
        
        # Add GPU configuration if available
        if self._has_gpu():
            cmd.extend([
                "--tensor-parallel-size", "1",
                "--gpu-memory-utilization", str(settings.vllm_gpu_memory_utilization)
            ])
            logger.info("GPU detected, enabling GPU acceleration")
        else:
            logger.warning("No GPU detected, vLLM will run on CPU (much slower)")
            # For CPU-only mode, limit memory usage
            cmd.extend([
                "--enforce-eager",
                "--max-num-batched-tokens", "512"
            ])
        
        return cmd
    
    def _has_gpu(self) -> bool:
        """Check if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available() and torch.cuda.device_count() > 0
        except ImportError:
            return False
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if port is already in use"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                return True
        return False
    
    async def _wait_for_vllm_ready(self) -> bool:
        """Wait for vLLM service to be ready"""
        start_time = time.time()
        logger.info(f"Waiting for vLLM to be ready (timeout: {self.startup_timeout}s)...")
        
        while time.time() - start_time < self.startup_timeout:
            if self.process and self.process.poll() is not None:
                # Process has terminated
                stdout, stderr = self.process.communicate()
                logger.error(f"vLLM process terminated unexpectedly")
                logger.error(f"STDOUT: {stdout.decode()}")
                logger.error(f"STDERR: {stderr.decode()}")
                return False
            
            if await self._is_vllm_running():
                elapsed = time.time() - start_time
                logger.info(f"vLLM service is ready (took {elapsed:.1f}s)")
                return True
            
            # Log progress every 30 seconds
            elapsed = time.time() - start_time
            if int(elapsed) % 30 == 0:
                logger.info(f"Still waiting for vLLM... ({elapsed:.0f}s elapsed)")
            
            await asyncio.sleep(self.health_check_interval)
        
        logger.error(f"vLLM failed to start within {self.startup_timeout} seconds")
        return False
    
    async def _is_vllm_running(self) -> bool:
        """Check if vLLM service is running and responsive"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.vllm_base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    async def stop_vllm_service(self) -> bool:
        """Stop vLLM service gracefully"""
        if not self.process:
            logger.info("No vLLM process to stop")
            return True
        
        logger.info("Stopping vLLM service...")
        
        try:
            # Send SIGTERM to process group
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=30)
                logger.info("vLLM service stopped gracefully")
                return True
            except subprocess.TimeoutExpired:
                # Force kill if needed
                logger.warning("vLLM service didn't stop gracefully, force killing...")
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                self.process.wait()
                logger.info("vLLM service force stopped")
                return True
                
        except Exception as e:
            logger.error(f"Error stopping vLLM service: {e}")
            return False
        finally:
            self.process = None
    
    async def restart_vllm_service(self, model_name: Optional[str] = None) -> bool:
        """Restart vLLM service"""
        logger.info("Restarting vLLM service...")
        await self.stop_vllm_service()
        await asyncio.sleep(2)  # Brief pause
        return await self.start_vllm_service(model_name)
    
    def get_vllm_status(self) -> dict:
        """Get current status of vLLM service"""
        status = {
            "process_running": self.process is not None and self.process.poll() is None,
            "process_pid": self.process.pid if self.process else None,
            "port": self.vllm_port,
            "model": settings.vllm_model_name,
            "auto_start_enabled": settings.vllm_auto_start,
            "gpu_available": self._has_gpu()
        }
        
        if self.process:
            try:
                proc = psutil.Process(self.process.pid)
                status.update({
                    "memory_usage_mb": round(proc.memory_info().rss / 1024 / 1024, 1),
                    "cpu_percent": round(proc.cpu_percent(), 1),
                    "create_time": proc.create_time(),
                    "status": proc.status()
                })
            except psutil.NoSuchProcess:
                status["process_running"] = False
        
        return status
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup"""
        await self.stop_vllm_service()


# Global vLLM manager instance
vllm_manager = VLLMManager() 