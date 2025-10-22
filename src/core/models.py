"""
Domain models - data contracts for the application.
Enforces type safety and clear API boundaries.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ProcessingStatus(Enum):
    """Processing state enumeration."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TranscriptionResult:
    """
    Result from speech recognition.
    Immutable for thread safety.
    """
    
    text: str
    is_partial: bool
    timestamp: datetime
    confidence: Optional[float] = None
    
    @property
    def is_final(self) -> bool:
        """Whether this is a final transcription."""
        return not self.is_partial


@dataclass(frozen=True)
class ProcessingRequest:
    """
    Request to process transcribed text with BitNet.
    Clean input contract.
    """
    
    transcript: str
    custom_prompt: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate request parameters.
        Returns (is_valid, error_message).
        """
        if not self.transcript or not self.transcript.strip():
            return False, "Transcript cannot be empty"
        
        if self.max_tokens is not None and self.max_tokens < 1:
            return False, "max_tokens must be positive"
        
        if self.temperature is not None:
            if not 0.0 <= self.temperature <= 2.0:
                return False, "temperature must be between 0.0 and 2.0"
        
        return True, None


@dataclass(frozen=True)
class ProcessingResult:
    """
    Result from BitNet processing.
    Enforces strict API contract - always returns structured data.
    """
    
    status: ProcessingStatus
    processed_text: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[float] = None
    
    @property
    def is_success(self) -> bool:
        """Whether processing succeeded."""
        return self.status == ProcessingStatus.COMPLETED
    
    @property
    def is_error(self) -> bool:
        """Whether processing failed."""
        return self.status == ProcessingStatus.FAILED
    
    def get_text_or_error(self) -> str:
        """
        Get processed text or error message.
        Always returns a string for display purposes.
        """
        if self.is_success and self.processed_text:
            return self.processed_text
        elif self.error_message:
            return f"Error: {self.error_message}"
        else:
            return f"Processing {self.status.value}"
    
    @classmethod
    def success(
        cls,
        processed_text: str,
        processing_time_ms: Optional[float] = None
    ) -> "ProcessingResult":
        """Factory method for successful result."""
        return cls(
            status=ProcessingStatus.COMPLETED,
            processed_text=processed_text,
            processing_time_ms=processing_time_ms
        )
    
    @classmethod
    def failure(
        cls,
        error_message: str,
        processing_time_ms: Optional[float] = None
    ) -> "ProcessingResult":
        """Factory method for failed result."""
        return cls(
            status=ProcessingStatus.FAILED,
            error_message=error_message,
            processing_time_ms=processing_time_ms
        )
    
    @classmethod
    def cancelled(cls) -> "ProcessingResult":
        """Factory method for cancelled result."""
        return cls(
            status=ProcessingStatus.CANCELLED,
            error_message="Processing cancelled by user"
        )
