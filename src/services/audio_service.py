"""
Audio capture and speech recognition service.
Abstracts VOSK implementation details from UI layer.
"""

from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from typing import Callable, Optional
import json
import threading

import sounddevice as sd
import vosk

from ..core.config import AudioConfig, VoskConfig
from ..core.models import TranscriptionResult


class AudioService:
    """
    Manages audio capture and speech-to-text conversion.
    Thread-safe, stateful service with clean lifecycle.
    """
    
    def __init__(
        self,
        vosk_config: VoskConfig,
        audio_config: Optional[AudioConfig] = None
    ):
        self._vosk_config = vosk_config
        self._audio_config = audio_config or AudioConfig()
        
        # State
        self._model: Optional[vosk.Model] = None
        self._recognizer: Optional[vosk.KaldiRecognizer] = None
        self._stream: Optional[sd.RawInputStream] = None
        self._audio_queue: Queue = Queue()
        self._processing_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        
        # Callbacks
        self._on_partial_result: Optional[Callable[[TranscriptionResult], None]] = None
        self._on_final_result: Optional[Callable[[TranscriptionResult], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None
    
    def initialize(self) -> tuple[bool, Optional[str]]:
        """
        Initialize VOSK model.
        Returns (success, error_message).
        """
        try:
            model_path = str(self._vosk_config.model_path)
            self._model = vosk.Model(model_path)
            self._recognizer = vosk.KaldiRecognizer(
                self._model,
                self._audio_config.sample_rate
            )
            return True, None
        except Exception as e:
            error = f"Failed to initialize VOSK model: {e}"
            return False, error
    
    def set_callbacks(
        self,
        on_partial: Optional[Callable[[TranscriptionResult], None]] = None,
        on_final: Optional[Callable[[TranscriptionResult], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> None:
        """Register callback handlers."""
        self._on_partial_result = on_partial
        self._on_final_result = on_final
        self._on_error = on_error
    
    def start_recording(self) -> tuple[bool, Optional[str]]:
        """
        Start audio capture and recognition.
        Returns (success, error_message).
        """
        with self._lock:
            if self._running:
                return False, "Already recording"
            
            if not self._model or not self._recognizer:
                return False, "Service not initialized"
            
            try:
                # Start audio stream
                self._stream = sd.RawInputStream(
                    samplerate=self._audio_config.sample_rate,
                    blocksize=self._audio_config.block_size,
                    channels=self._audio_config.channels,
                    dtype=self._audio_config.dtype,
                    callback=self._audio_callback
                )
                
                # Start processing thread
                self._running = True
                self._processing_thread = threading.Thread(
                    target=self._process_audio,
                    daemon=True
                )
                self._processing_thread.start()
                self._stream.start()
                
                return True, None
                
            except Exception as e:
                self._running = False
                error = f"Failed to start recording: {e}"
                return False, error
    
    def stop_recording(self) -> tuple[bool, Optional[str]]:
        """
        Stop audio capture gracefully.
        Returns (success, error_message).
        """
        with self._lock:
            if not self._running:
                return False, "Not recording"
            
            try:
                self._running = False
                
                # Stop stream
                if self._stream:
                    self._stream.stop()
                    self._stream.close()
                    self._stream = None
                
                # Signal thread to stop
                self._audio_queue.put(None)
                
                # Wait for processing thread
                if self._processing_thread:
                    self._processing_thread.join(timeout=2.0)
                    self._processing_thread = None
                
                # Emit final result
                if self._recognizer:
                    final_json = self._recognizer.FinalResult()
                    self._handle_final_result(final_json)
                
                return True, None
                
            except Exception as e:
                error = f"Error stopping recording: {e}"
                return False, error
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._running
    
    def shutdown(self) -> None:
        """Clean shutdown of all resources."""
        if self._running:
            self.stop_recording()
        
        self._model = None
        self._recognizer = None
    
    # Private methods
    
    def _audio_callback(self, indata, frames, time, status) -> None:
        """Handle incoming audio data."""
        if status and self._on_error:
            self._on_error(f"Audio stream status: {status}")
        
        if self._running:
            self._audio_queue.put(bytes(indata))
    
    def _process_audio(self) -> None:
        """Process audio data from queue (runs in separate thread)."""
        while self._running:
            try:
                # Get audio data with timeout
                data = self._audio_queue.get(timeout=0.1)
                
                # None signals stop
                if data is None:
                    break
                
                # Process with recognizer
                if self._recognizer.AcceptWaveform(data):
                    result_json = self._recognizer.Result()
                    self._handle_final_result(result_json)
                else:
                    partial_json = self._recognizer.PartialResult()
                    self._handle_partial_result(partial_json)
                    
            except Empty:
                continue
            except Exception as e:
                if self._on_error:
                    self._on_error(f"Processing error: {e}")
    
    def _handle_partial_result(self, result_json: str) -> None:
        """Handle partial recognition result."""
        try:
            data = json.loads(result_json)
            text = data.get("partial", "").strip()
            
            if text and self._on_partial_result:
                result = TranscriptionResult(
                    text=text,
                    is_partial=True,
                    timestamp=datetime.now()
                )
                self._on_partial_result(result)
                
        except Exception as e:
            if self._on_error:
                self._on_error(f"Error parsing partial result: {e}")
    
    def _handle_final_result(self, result_json: str) -> None:
        """Handle final recognition result."""
        try:
            data = json.loads(result_json)
            text = data.get("text", "").strip()
            
            if text and self._on_final_result:
                result = TranscriptionResult(
                    text=text,
                    is_partial=False,
                    timestamp=datetime.now()
                )
                self._on_final_result(result)
                
        except Exception as e:
            if self._on_error:
                self._on_error(f"Error parsing final result: {e}")
