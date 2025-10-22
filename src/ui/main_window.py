"""
Main window - thin UI orchestration layer.
Delegates to services, never contains business logic.
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QMessageBox, QTabWidget, QLineEdit,
    QSpinBox, QDoubleSpinBox, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QTextCursor

from ..core.config import Config
from ..core.models import TranscriptionResult, ProcessingRequest, ProcessingResult
from ..services import AudioService, InferenceService, ClipboardService, ChatService
from .styles import get_stylesheet, get_recording_button_style


class InferenceWorker(QObject):
    """Worker for running inference in background QThread."""
    
    finished = pyqtSignal(ProcessingResult)
    status_update = pyqtSignal(str)
    
    def __init__(self, service: InferenceService, request: ProcessingRequest):
        super().__init__()
        self._service = service
        self._request = request
    
    def run(self) -> None:
        """Execute inference and emit result."""
        result = self._service.process(
            self._request,
            callback_status=lambda msg: self.status_update.emit(msg)
        )
        self.finished.emit(result)


class ChatWorker(QObject):
    """Worker for running chat inference in background QThread."""
    
    finished = pyqtSignal(bool, str, str)  # success, message, error
    status_update = pyqtSignal(str)
    
    def __init__(self, service: ChatService, message: str):
        super().__init__()
        self._service = service
        self._message = message
    
    def run(self) -> None:
        """Execute chat and emit result."""
        response = self._service.send_message(
            self._message,
            callback_status=lambda msg: self.status_update.emit(msg)
        )
        self.finished.emit(response.success, response.message, response.error or "")


class MainWindow(QMainWindow):
    """
    Main application window.
    Orchestrates UI and delegates to services.
    """
    
    # Internal signals for thread-safe UI updates
    _partial_received = pyqtSignal(str)
    _final_received = pyqtSignal(str)
    _error_received = pyqtSignal(str)
    
    def __init__(self, config: Config):
        super().__init__()
        self._config = config
        
        # Services
        self._audio_service: Optional[AudioService] = None
        self._inference_service: Optional[InferenceService] = None
        self._chat_service: Optional[ChatService] = None
        
        # State
        self._transcript_accumulator: list[str] = []
        self._inference_thread: Optional[QThread] = None
        self._inference_worker: Optional[InferenceWorker] = None
        self._chat_thread: Optional[QThread] = None
        self._chat_worker: Optional[ChatWorker] = None
        
        # Connect internal signals to UI update slots
        self._partial_received.connect(self._update_partial_display)
        self._final_received.connect(self._update_transcript_display)
        self._error_received.connect(lambda msg: self._show_error("Audio Error", msg))
        
        # Initialize UI
        self._init_ui()
        self._init_services()
    
    def _init_ui(self) -> None:
        """Initialize user interface."""
        self.setWindowTitle(self._config.ui.window_title)
        self.setGeometry(
            100, 100,
            self._config.ui.window_width,
            self._config.ui.window_height
        )
        self.setStyleSheet(get_stylesheet(self._config.ui))
        
        # Central widget with tabs
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget
        self._tabs = QTabWidget()
        main_layout.addWidget(self._tabs)
        
        # Chat tab (first)
        chat_tab = self._create_chat_tab()
        self._tabs.addTab(chat_tab, "Chat")
        
        # Voice transcription tab (second)
        voice_tab = QWidget()
        voice_layout = QHBoxLayout(voice_tab)
        voice_layout.setContentsMargins(16, 16, 16, 16)
        
        left_panel = self._create_input_panel()
        voice_layout.addLayout(left_panel, stretch=3)
        
        right_panel = self._create_output_panel()
        voice_layout.addLayout(right_panel, stretch=2)
        
        self._tabs.addTab(voice_tab, "Voice Transcription")
        
        # Settings tab (third)
        settings_tab = self._create_settings_tab()
        self._tabs.addTab(settings_tab, "Settings")
    
    def _create_input_panel(self) -> QVBoxLayout:
        """Create left input panel."""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Title
        title = QLabel("Voice Recording")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Custom prompt
        prompt_label = QLabel("Processing Instructions:")
        layout.addWidget(prompt_label)
        
        self._prompt_input = QTextEdit()
        self._prompt_input.setPlaceholderText(
            "Enter custom instructions for note processing..."
        )
        self._prompt_input.setMaximumHeight(80)
        layout.addWidget(self._prompt_input)
        
        # Partial transcription
        partial_label = QLabel("Current Speech:")
        layout.addWidget(partial_label)
        
        self._partial_display = QTextEdit()
        self._partial_display.setReadOnly(True)
        self._partial_display.setMaximumHeight(60)
        layout.addWidget(self._partial_display)
        
        # Full transcription
        transcript_label = QLabel("Transcript:")
        layout.addWidget(transcript_label)
        
        self._transcript_display = QTextEdit()
        self._transcript_display.setReadOnly(True)
        layout.addWidget(self._transcript_display)
        
        # Status
        self._status_label = QLabel("Ready")
        self._status_label.setProperty("status", True)
        layout.addWidget(self._status_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self._record_button = QPushButton("Start Recording")
        self._record_button.clicked.connect(self._toggle_recording)
        button_layout.addWidget(self._record_button)
        
        self._process_button = QPushButton("Generate Notes")
        self._process_button.clicked.connect(self._start_processing)
        self._process_button.setEnabled(False)
        button_layout.addWidget(self._process_button)
        
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self._clear_all)
        button_layout.addWidget(clear_button)
        
        layout.addLayout(button_layout)
        
        return layout
    
    def _create_output_panel(self) -> QVBoxLayout:
        """Create right output panel."""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Title
        title = QLabel("Generated Notes")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Output display
        self._output_display = QTextEdit()
        self._output_display.setReadOnly(True)
        layout.addWidget(self._output_display)
        
        # Copy button
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self._copy_output)
        layout.addWidget(copy_button)
        
        return layout
    
    def _create_chat_tab(self) -> QWidget:
        """Create chat interface tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("Chat with BitNet")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Chat history display
        self._chat_display = QTextEdit()
        self._chat_display.setReadOnly(True)
        layout.addWidget(self._chat_display)
        
        # Status label for chat
        self._chat_status_label = QLabel("Ready")
        self._chat_status_label.setProperty("status", True)
        layout.addWidget(self._chat_status_label)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        self._chat_input = QLineEdit()
        self._chat_input.setPlaceholderText("Type your message here...")
        self._chat_input.returnPressed.connect(self._send_chat_message)
        input_layout.addWidget(self._chat_input)
        
        self._chat_send_button = QPushButton("Send")
        self._chat_send_button.clicked.connect(self._send_chat_message)
        input_layout.addWidget(self._chat_send_button)
        
        layout.addLayout(input_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        clear_chat_button = QPushButton("Clear History")
        clear_chat_button.clicked.connect(self._clear_chat)
        button_layout.addWidget(clear_chat_button)
        
        copy_chat_button = QPushButton("Copy Chat")
        copy_chat_button.clicked.connect(self._copy_chat)
        button_layout.addWidget(copy_chat_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return widget
    
    def _create_settings_tab(self) -> QWidget:
        """Create settings interface tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("BitNet Settings")
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # BitNet status indicator
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout()
        
        self._bitnet_status_label = QLabel("Checking...")
        self._bitnet_status_label.setProperty("status", True)
        status_layout.addWidget(self._bitnet_status_label)
        
        check_button = QPushButton("Check BitNet Status")
        check_button.clicked.connect(self._check_bitnet_status)
        status_layout.addWidget(check_button)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Connection settings
        conn_group = QGroupBox("Connection")
        conn_layout = QFormLayout()
        conn_layout.setSpacing(8)
        
        self._endpoint_input = QLineEdit()
        self._endpoint_input.setText(self._config.bitnet.endpoint_url if self._config.bitnet else "http://localhost:8081/completion")
        conn_layout.addRow("Endpoint URL:", self._endpoint_input)
        
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Inference settings
        inference_group = QGroupBox("Inference Parameters")
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # Max tokens
        self._max_tokens_spin = QSpinBox()
        self._max_tokens_spin.setRange(128, 8192)
        self._max_tokens_spin.setValue(self._config.bitnet.max_tokens if self._config.bitnet else 2048)
        self._max_tokens_spin.setSingleStep(128)
        form_layout.addRow("Max Tokens:", self._max_tokens_spin)
        
        # Temperature
        self._temperature_spin = QDoubleSpinBox()
        self._temperature_spin.setRange(0.0, 2.0)
        self._temperature_spin.setValue(self._config.bitnet.temperature if self._config.bitnet else 0.7)
        self._temperature_spin.setSingleStep(0.1)
        self._temperature_spin.setDecimals(2)
        form_layout.addRow("Temperature:", self._temperature_spin)
        
        # Timeout
        self._timeout_spin = QDoubleSpinBox()
        self._timeout_spin.setRange(5.0, 120.0)
        self._timeout_spin.setValue(self._config.bitnet.timeout_seconds if self._config.bitnet else 30.0)
        self._timeout_spin.setSingleStep(5.0)
        self._timeout_spin.setDecimals(1)
        self._timeout_spin.setSuffix(" seconds")
        form_layout.addRow("Timeout:", self._timeout_spin)
        
        # Repeat penalty
        self._repeat_penalty_spin = QDoubleSpinBox()
        self._repeat_penalty_spin.setRange(1.0, 2.0)
        self._repeat_penalty_spin.setValue(self._config.bitnet.repeat_penalty if self._config.bitnet else 1.15)
        self._repeat_penalty_spin.setSingleStep(0.05)
        self._repeat_penalty_spin.setDecimals(2)
        form_layout.addRow("Repeat Penalty:", self._repeat_penalty_spin)
        
        # Repeat last N
        self._repeat_last_n_spin = QSpinBox()
        self._repeat_last_n_spin.setRange(0, 256)
        self._repeat_last_n_spin.setValue(self._config.bitnet.repeat_last_n if self._config.bitnet else 64)
        self._repeat_last_n_spin.setSingleStep(16)
        form_layout.addRow("Repeat Last N:", self._repeat_last_n_spin)
        
        # Top P
        self._top_p_spin = QDoubleSpinBox()
        self._top_p_spin.setRange(0.0, 1.0)
        self._top_p_spin.setValue(self._config.bitnet.top_p if self._config.bitnet else 0.9)
        self._top_p_spin.setSingleStep(0.05)
        self._top_p_spin.setDecimals(2)
        form_layout.addRow("Top P:", self._top_p_spin)
        
        # Top K
        self._top_k_spin = QSpinBox()
        self._top_k_spin.setRange(1, 100)
        self._top_k_spin.setValue(self._config.bitnet.top_k if self._config.bitnet else 40)
        self._top_k_spin.setSingleStep(5)
        form_layout.addRow("Top K:", self._top_k_spin)
        
        inference_group.setLayout(form_layout)
        layout.addWidget(inference_group)
        
        # System prompt
        prompt_label = QLabel("System Prompt for Notes:")
        layout.addWidget(prompt_label)
        
        self._system_prompt_edit = QTextEdit()
        self._system_prompt_edit.setPlaceholderText("Enter system prompt for note generation...")
        self._system_prompt_edit.setText(self._config.bitnet.system_prompt if self._config.bitnet else "")
        self._system_prompt_edit.setMaximumHeight(120)
        layout.addWidget(self._system_prompt_edit)
        
        # Apply button
        apply_button = QPushButton("Apply Settings")
        apply_button.clicked.connect(self._apply_settings)
        layout.addWidget(apply_button)
        
        # Info label
        info_label = QLabel("Note: Settings apply to new requests only.")
        info_label.setProperty("status", True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        return widget
    
    def _init_services(self) -> None:
        """Initialize backend services."""
        # Audio service
        self._audio_service = AudioService(
            vosk_config=self._config.vosk,
            audio_config=self._config.audio
        )
        
        success, error = self._audio_service.initialize()
        if not success:
            self._show_error(f"Audio Service Error", error or "Unknown error")
            return
        
        self._audio_service.set_callbacks(
            on_partial=self._handle_partial_transcript,
            on_final=self._handle_final_transcript,
            on_error=self._handle_audio_error
        )
        
        # Inference service
        if self._config.bitnet:
            self._inference_service = InferenceService(self._config.bitnet)
            self._chat_service = ChatService(self._config.bitnet)
            # Check BitNet status on startup
            self._check_bitnet_status()
        else:
            self._show_warning(
                "BitNet Not Configured",
                "BitNet model path not set. Set BITNET_MODEL_PATH environment variable."
            )
    
    # Event handlers
    
    def _toggle_recording(self) -> None:
        """Toggle audio recording."""
        if not self._audio_service:
            return
        
        if self._audio_service.is_recording():
            self._stop_recording()
        else:
            self._start_recording()
    
    def _start_recording(self) -> None:
        """Start audio recording."""
        if not self._audio_service:
            return
        
        success, error = self._audio_service.start_recording()
        if not success:
            self._show_error("Recording Error", error or "Failed to start")
            return
        
        self._record_button.setText("Stop Recording")
        self._record_button.setStyleSheet(
            get_recording_button_style(True, self._config.ui)
        )
        self._status_label.setText("Recording...")
    
    def _stop_recording(self) -> None:
        """Stop audio recording."""
        if not self._audio_service:
            return
        
        success, error = self._audio_service.stop_recording()
        if not success:
            self._show_error("Recording Error", error or "Failed to stop")
        
        self._record_button.setText("Start Recording")
        self._record_button.setStyleSheet(
            get_recording_button_style(False, self._config.ui)
        )
        self._status_label.setText("Ready")
        
        # Enable processing if we have text
        has_text = bool(self._transcript_display.toPlainText().strip())
        self._process_button.setEnabled(has_text and self._inference_service is not None)
    
    def _start_processing(self) -> None:
        """Start text processing with BitNet."""
        try:
            if not self._inference_service:
                self._show_warning("Service Unavailable", "BitNet service not initialized")
                return
            
            transcript = self._transcript_display.toPlainText().strip()
            if not transcript:
                self._show_warning("No Transcript", "Nothing to process")
                return
            
            custom_prompt = self._prompt_input.toPlainText().strip()
            
            request = ProcessingRequest(
                transcript=transcript,
                custom_prompt=custom_prompt if custom_prompt else None
            )
            
            # Validate request
            is_valid, error = request.validate()
            if not is_valid:
                self._show_error("Invalid Request", error or "Unknown validation error")
                return
            
            # Update UI state
            self._process_button.setEnabled(False)
            self._status_label.setText("⏳ BitNet processing...")
            self._status_label.setStyleSheet("color: #606060;")
            
            # Run inference in background using QThread
            self._inference_thread = QThread()
            self._inference_worker = InferenceWorker(self._inference_service, request)
            self._inference_worker.moveToThread(self._inference_thread)
            
            # Connect signals
            self._inference_thread.started.connect(self._inference_worker.run)
            self._inference_worker.finished.connect(self._handle_processing_complete)
            self._inference_worker.finished.connect(self._inference_thread.quit)
            self._inference_worker.status_update.connect(self._update_status)
            
            # Start thread
            self._inference_thread.start()
        except Exception as e:
            self._show_error("Processing Error", f"Failed to start processing: {str(e)}")
            self._process_button.setEnabled(True)
            self._status_label.setText("❌ Error")
            self._status_label.setStyleSheet("color: #C41E3A;")
    
    def _clear_all(self) -> None:
        """Clear all text fields."""
        self._partial_display.clear()
        self._transcript_display.clear()
        self._output_display.clear()
        self._transcript_accumulator.clear()
        self._status_label.setText("Ready")
        self._process_button.setEnabled(False)
    
    def _copy_output(self) -> None:
        """Copy output to clipboard."""
        text = self._output_display.toPlainText()
        if not text:
            return
        
        success, error = ClipboardService.copy_text(text)
        if success:
            self._status_label.setText("Copied to clipboard")
        else:
            self._show_error("Copy Failed", error or "Unknown error")
    
    # Callbacks (called from audio service thread - must emit signals, not modify UI directly)
    
    def _handle_partial_transcript(self, result: TranscriptionResult) -> None:
        """Handle partial transcription - emit signal for thread safety."""
        self._partial_received.emit(result.text)
    
    def _handle_final_transcript(self, result: TranscriptionResult) -> None:
        """Handle final transcription - emit signal for thread safety."""
        self._final_received.emit(result.text)
    
    def _handle_audio_error(self, error: str) -> None:
        """Handle audio service error - emit signal for thread safety."""
        self._error_received.emit(error)
    
    # UI update slots (safe to call from main thread only)
    
    def _update_partial_display(self, text: str) -> None:
        """Update partial transcript display."""
        self._partial_display.setPlainText(text)
    
    def _update_transcript_display(self, text: str) -> None:
        """Update full transcript display."""
        self._transcript_accumulator.append(text)
        full_text = " ".join(self._transcript_accumulator)
        self._transcript_display.setPlainText(full_text)
        self._partial_display.clear()
        
        # Enable processing button
        if self._inference_service:
            self._process_button.setEnabled(True)
    
    def _handle_processing_complete(self, result: ProcessingResult) -> None:
        """Handle inference completion."""
        self._process_button.setEnabled(True)
        
        if result.is_success:
            self._output_display.setPlainText(result.processed_text or "")
            time_ms = result.processing_time_ms or 0
            self._status_label.setText(f"✅ Complete ({time_ms:.0f}ms)")
            self._status_label.setStyleSheet("color: #2D5016;")
        else:
            self._show_error("Processing Error", result.error_message or "Unknown error")
            self._status_label.setText("❌ Error")
            self._status_label.setStyleSheet("color: #C41E3A;")
    
    def _update_status(self, message: str) -> None:
        """Update status label."""
        self._status_label.setText(message)
        # Reset to default color when just updating message
        if not any(x in message for x in ["⏳", "✅", "❌"]):
            self._status_label.setStyleSheet("")
    
    # Chat event handlers
    
    def _send_chat_message(self) -> None:
        """Send chat message to BitNet."""
        if not self._chat_service:
            self._show_warning("Service Unavailable", "Chat service not initialized")
            return
        
        message = self._chat_input.text().strip()
        if not message:
            return
        
        # Display user message
        self._append_chat_message("You", message)
        self._chat_input.clear()
        
        # Update UI state
        self._chat_send_button.setEnabled(False)
        self._chat_input.setEnabled(False)
        self._chat_status_label.setText("⏳ BitNet thinking...")
        self._chat_status_label.setStyleSheet("color: #606060;")
        
        # Run chat in background using QThread
        self._chat_thread = QThread()
        self._chat_worker = ChatWorker(self._chat_service, message)
        self._chat_worker.moveToThread(self._chat_thread)
        
        # Connect signals
        self._chat_thread.started.connect(self._chat_worker.run)
        self._chat_worker.finished.connect(self._handle_chat_response)
        self._chat_worker.finished.connect(self._chat_thread.quit)
        self._chat_worker.status_update.connect(self._update_chat_status)
        
        # Start thread
        self._chat_thread.start()
    
    def _handle_chat_response(self, success: bool, message: str, error: str) -> None:
        """Handle chat response."""
        self._chat_send_button.setEnabled(True)
        self._chat_input.setEnabled(True)
        self._chat_input.setFocus()
        
        if success:
            self._append_chat_message("Assistant", message)
            self._chat_status_label.setText("✅ Ready")
            self._chat_status_label.setStyleSheet("color: #2D5016;")
        else:
            self._show_error("Chat Error", error)
            self._chat_status_label.setText("❌ Error")
            self._chat_status_label.setStyleSheet("color: #C41E3A;")
    
    def _update_chat_status(self, message: str) -> None:
        """Update chat status label."""
        self._chat_status_label.setText(message)
        # Reset to default color when just updating message
        if not any(x in message for x in ["⏳", "✅", "❌"]):
            self._chat_status_label.setStyleSheet("")
    
    def _append_chat_message(self, role: str, message: str) -> None:
        """Append message to chat display."""
        cursor = self._chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Add separator if not first message
        if not self._chat_display.toPlainText():
            cursor.insertText(f"{role}: {message}\n")
        else:
            cursor.insertText(f"\n{role}: {message}\n")
        
        # Scroll to bottom
        self._chat_display.setTextCursor(cursor)
        self._chat_display.ensureCursorVisible()
    
    def _clear_chat(self) -> None:
        """Clear chat history."""
        if self._chat_service:
            self._chat_service.clear_history()
        self._chat_display.clear()
        self._chat_status_label.setText("Ready")
    
    def _copy_chat(self) -> None:
        """Copy chat history to clipboard."""
        text = self._chat_display.toPlainText()
        if not text:
            return
        
        success, error = ClipboardService.copy_text(text)
        if success:
            self._chat_status_label.setText("Copied to clipboard")
        else:
            self._show_error("Copy Failed", error or "Unknown error")
    
    # Settings handlers
    
    def _check_bitnet_status(self) -> None:
        """Check if BitNet is available."""
        if not self._config.bitnet:
            self._bitnet_status_label.setText("❌ Not configured")
            self._bitnet_status_label.setStyleSheet("color: #C41E3A;")
            return
        
        endpoint = self._endpoint_input.text().strip() if hasattr(self, '_endpoint_input') else self._config.bitnet.endpoint_url
        
        # Check availability
        is_available, error = InferenceService.check_availability(endpoint)
        
        if is_available:
            self._bitnet_status_label.setText(f"✅ Connected to {endpoint}")
            self._bitnet_status_label.setStyleSheet("color: #2D5016;")
        else:
            self._bitnet_status_label.setText(f"❌ {error or 'Not available'}")
            self._bitnet_status_label.setStyleSheet("color: #C41E3A;")
    
    def _apply_settings(self) -> None:
        """Apply settings changes."""
        if not self._config.bitnet:
            self._show_warning("No Configuration", "BitNet not configured")
            return
        
        # Update config values (create new immutable config)
        from dataclasses import replace
        
        new_endpoint = self._endpoint_input.text().strip()
        
        new_bitnet_config = replace(
            self._config.bitnet,
            endpoint_url=new_endpoint,
            max_tokens=self._max_tokens_spin.value(),
            temperature=self._temperature_spin.value(),
            timeout_seconds=self._timeout_spin.value(),
            repeat_penalty=self._repeat_penalty_spin.value(),
            repeat_last_n=self._repeat_last_n_spin.value(),
            top_p=self._top_p_spin.value(),
            top_k=self._top_k_spin.value(),
            system_prompt=self._system_prompt_edit.toPlainText().strip()
        )
        
        self._config = replace(self._config, bitnet=new_bitnet_config)
        
        # Recreate services with new config
        if self._inference_service:
            self._inference_service = InferenceService(new_bitnet_config)
        if self._chat_service:
            self._chat_service = ChatService(new_bitnet_config)
        
        # Check status with new endpoint
        self._check_bitnet_status()
        
        QMessageBox.information(self, "Settings Applied", "Settings have been updated successfully.")
    
    # UI helpers
    
    def _show_error(self, title: str, message: str) -> None:
        """Show error dialog."""
        QMessageBox.critical(self, title, message)
    
    def _show_warning(self, title: str, message: str) -> None:
        """Show warning dialog."""
        QMessageBox.warning(self, title, message)
    
    def closeEvent(self, event) -> None:
        """Handle window close."""
        # Stop recording if active
        if self._audio_service and self._audio_service.is_recording():
            self._audio_service.stop_recording()
        
        # Cancel processing if active
        if self._inference_service:
            self._inference_service.cancel()
        
        # Cancel chat if active
        if self._chat_service:
            self._chat_service.cancel()
        
        # Cleanup
        if self._audio_service:
            self._audio_service.shutdown()
        
        event.accept()
