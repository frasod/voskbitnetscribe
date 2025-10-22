"""
BitNet inference service for text processing.
Abstracts model inference from UI and business logic.
"""

import json
import time
from pathlib import Path
from typing import Optional
import threading

import requests

from ..core.config import BitNetConfig
from ..core.models import ProcessingRequest, ProcessingResult, ProcessingStatus


class InferenceService:
    """
    Local BitNet inference service.
    Uses HTTP API endpoint for text generation.
    """
    
    def __init__(self, config: BitNetConfig):
        self._config = config
        self._lock = threading.Lock()
        self._session = requests.Session()
        self._cancelled = False
    
    def process(
        self,
        request: ProcessingRequest,
        callback_status: Optional[callable] = None
    ) -> ProcessingResult:
        """
        Process text with BitNet model.
        Blocking call - run in separate thread for async operation.
        
        Returns structured ProcessingResult (never throws for API errors).
        """
        start_time = time.time()
        
        # Validate request
        is_valid, error_msg = request.validate()
        if not is_valid:
            return ProcessingResult.failure(
                error_message=f"Invalid request: {error_msg}",
                processing_time_ms=0
            )
        
        # Build prompt
        system_prompt = self._config.system_prompt
        user_prompt = request.custom_prompt or "Convert this transcript into clear notes:"
        full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nTranscript:\n{request.transcript}"
        
        try:
            if callback_status:
                callback_status("Initializing BitNet inference...")
            
            # Execute BitNet inference
            # NOTE: Adjust command based on actual BitNet CLI/API
            result_text = self._execute_inference(
                prompt=full_prompt,
                max_tokens=request.max_tokens or self._config.max_tokens,
                temperature=request.temperature or self._config.temperature,
                callback_status=callback_status
            )
            
            # Check if cancelled
            if self._cancelled:
                self._cancelled = False
                return ProcessingResult.cancelled()
            
            processing_time = (time.time() - start_time) * 1000
            
            return ProcessingResult.success(
                processed_text=result_text,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return ProcessingResult.failure(
                error_message=str(e),
                processing_time_ms=processing_time
            )
    
    def cancel(self) -> None:
        """Cancel current inference operation."""
        with self._lock:
            self._cancelled = True
    
    def _execute_inference(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        callback_status: Optional[callable]
    ) -> str:
        """
        Execute BitNet inference via HTTP API.
        
        Endpoint: http://localhost:8081/completion
        Method: POST
        Content-Type: application/json
        """
        with self._lock:
            if self._cancelled:
                raise RuntimeError("Inference cancelled")
            
            if callback_status:
                callback_status("Sending request to BitNet...")
            
            # Build request payload
            payload = {
                "prompt": prompt,
                "n_predict": max_tokens,
                "temperature": temperature,
                "stop": [],
                "stream": False
            }
            
            try:
                # Send POST request
                response = self._session.post(
                    self._config.endpoint_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=self._config.timeout_seconds
                )
                
                # Check if cancelled during request
                if self._cancelled:
                    raise RuntimeError("Inference cancelled")
                
                # Check response status
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                generated_text = self._parse_response(data)
                
                if callback_status:
                    callback_status("Processing complete")
                
                return generated_text
                
            except requests.exceptions.Timeout:
                raise RuntimeError(
                    f"BitNet request timeout after {self._config.timeout_seconds}s. "
                    "Ensure BitNet server is running on http://localhost:8081"
                )
            except requests.exceptions.ConnectionError:
                raise RuntimeError(
                    "Cannot connect to BitNet server. "
                    "Ensure BitNet is running on http://localhost:8081"
                )
            except requests.exceptions.HTTPError as e:
                raise RuntimeError(
                    f"BitNet HTTP error {e.response.status_code}: {e.response.text}"
                )
            except Exception as e:
                raise RuntimeError(f"BitNet inference error: {e}")
    
    def _parse_response(self, data: dict) -> str:
        """
        Parse BitNet API response.
        Expected format: {"content": "generated text"}
        Adjust based on actual response structure.
        """
        # Common response formats:
        # Option 1: {"content": "text"}
        if "content" in data:
            return data["content"].strip()
        
        # Option 2: {"text": "text"}
        if "text" in data:
            return data["text"].strip()
        
        # Option 3: {"completion": "text"}
        if "completion" in data:
            return data["completion"].strip()
        
        # Option 4: {"choices": [{"text": "text"}]}
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "text" in choice:
                return choice["text"].strip()
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"].strip()
        
        # Fallback: return entire response as string
        return str(data)
    
    @staticmethod
    def check_availability(endpoint_url: str = "http://localhost:8081") -> tuple[bool, Optional[str]]:
        """
        Check if BitNet HTTP API is available.
        Returns (is_available, error_message).
        """
        try:
            # Try to connect to BitNet server (try health endpoint first, then root)
            health_url = f"{endpoint_url}/health" if not endpoint_url.endswith("/completion") else endpoint_url.replace("/completion", "/health")
            
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    return True, None
            except:
                # Health endpoint might not exist, try root
                root_url = endpoint_url.split("/completion")[0] if "/completion" in endpoint_url else endpoint_url
                response = requests.get(root_url, timeout=5)
                if response.status_code in [200, 404]:  # 404 is OK, server is responding
                    return True, None
            
            return False, f"BitNet server unhealthy (status {response.status_code})"
                
        except requests.exceptions.ConnectionError:
            return False, (
                f"Cannot connect to BitNet server at {endpoint_url}. "
                "Ensure BitNet is running."
            )
        except requests.exceptions.Timeout:
            return False, "BitNet server connection timeout"
        except Exception as e:
            return False, f"Error checking BitNet availability: {e}"
