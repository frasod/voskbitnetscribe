"""
Core domain models and configuration.
Clean separation of data contracts from implementation.
"""

from .config import Config, AudioConfig
from .models import (
    TranscriptionResult,
    ProcessingRequest,
    ProcessingResult,
)

__all__ = [
    "Config",
    "AudioConfig",
    "TranscriptionResult",
    "ProcessingRequest",
    "ProcessingResult",
]
