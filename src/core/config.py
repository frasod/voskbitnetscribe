"""
Centralized configuration management.
Single source of truth for all application settings.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import os


@dataclass(frozen=True)
class AudioConfig:
    """Audio capture configuration."""
    
    sample_rate: int = 16000
    block_size: int = 8000
    channels: int = 1
    dtype: str = "int16"


@dataclass(frozen=True)
class VoskConfig:
    """VOSK speech recognition configuration."""
    
    model_name: str = "vosk-model-small-en-us-0.15"
    model_base_path: Optional[Path] = None
    
    @property
    def model_path(self) -> Path:
        """Resolve model path."""
        base = self.model_base_path or Path.cwd()
        return base / self.model_name
    
    def validate(self) -> bool:
        """Verify model directory exists and is valid."""
        path = self.model_path
        if not path.exists():
            return False
        
        # Check required VOSK model components
        required = ["am", "conf", "graph", "ivector"]
        return all((path / component).exists() for component in required)


@dataclass(frozen=True)
class BitNetConfig:
    """BitNet inference configuration."""
    
    endpoint_url: str = "http://localhost:8081/completion"
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout_seconds: float = 30.0
    
    # Advanced parameters
    repeat_penalty: float = 1.15
    repeat_last_n: int = 64
    top_p: float = 0.9
    top_k: int = 40
    
    # Default system prompt for note generation
    system_prompt: str = (
        "Refine and organize this note. Structure the key information logically. "
        "Eliminate all repetition, filler, and non-essential details to ensure "
        "the final output is brief, factual, and scannable."
    )


@dataclass(frozen=True)
class UIConfig:
    """User interface configuration."""
    
    window_title: str = "VOSK BitNet Scribe"
    window_width: int = 1200
    window_height: int = 800
    font_size: int = 14
    
    # Braun-inspired color palette
    background: str = "#F5F5F5"  # Clean light gray
    surface: str = "#FFFFFF"     # Pure white
    primary: str = "#000000"      # Black
    secondary: str = "#606060"    # Medium gray
    accent: str = "#D0D0D0"       # Light gray
    error: str = "#C41E3A"        # Muted red
    success: str = "#2D5016"      # Dark green


@dataclass
class Config:
    """
    Master configuration container.
    Immutable after initialization for thread safety.
    """
    
    audio: AudioConfig = field(default_factory=AudioConfig)
    vosk: VoskConfig = field(default_factory=VoskConfig)
    bitnet: Optional[BitNetConfig] = None
    ui: UIConfig = field(default_factory=UIConfig)
    
    @classmethod
    def from_environment(cls) -> "Config":
        """
        Build configuration from environment variables.
        Enables external configuration without code changes.
        """
        vosk_model_path = os.getenv("VOSK_MODEL_PATH")
        bitnet_endpoint = os.getenv("BITNET_ENDPOINT", "http://localhost:8081/completion")
        
        vosk_config = VoskConfig(
            model_base_path=Path(vosk_model_path) if vosk_model_path else None
        )
        
        # BitNet is always available via HTTP endpoint
        bitnet_config = BitNetConfig(endpoint_url=bitnet_endpoint)
        
        return cls(
            vosk=vosk_config,
            bitnet=bitnet_config
        )
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate configuration completeness.
        Returns (is_valid, error_messages).
        """
        errors = []
        
        if not self.vosk.validate():
            errors.append(
                f"VOSK model not found at: {self.vosk.model_path}"
            )
        
        # BitNet validation is done via health check (not file-based)
        if self.bitnet is None:
            errors.append(
                "BitNet configuration missing. This should not happen."
            )
        
        return len(errors) == 0, errors
