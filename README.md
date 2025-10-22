# VOSK BitNet Scribe

A clean, modular speech-to-notes application combining VOSK speech recognition with local BitNet inference.

## Architecture Philosophy

This application follows **Braun design principles**: clean, purposeful, elegant. The architecture emphasizes:

- **Separation of Concerns**: UI, business logic, and infrastructure are completely decoupled
- **Clear Contracts**: All service interactions use typed data models
- **Minimalism**: No unnecessary code, dependencies, or complexity
- **Testability**: Core logic can be tested without UI dependencies

## Project Structure

```
src/
├── core/           # Domain models and configuration
│   ├── config.py   # Centralized configuration
│   └── models.py   # Data contracts (immutable)
├── services/       # Business logic layer
│   ├── audio_service.py      # VOSK speech recognition
│   ├── inference_service.py  # BitNet text processing
│   └── clipboard_service.py  # System integration
└── ui/             # Presentation layer
    ├── styles.py   # Separated styling (Braun aesthetic)
    └── main_window.py  # UI orchestration
main.py            # Entry point (lean)
```

## Requirements

- Python 3.8+
- VOSK model (vosk-model-small-en-us-0.15)
- BitNet server running on http://localhost:8081
- Microphone

## Installation

### Linux

```bash
# 1. Make scripts executable
chmod +x setup.sh start.sh

# 2. Run setup
./setup.sh

# 3. Download VOSK model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

### Configuration

Set environment variables:

```bash
# Optional: Custom VOSK model location
export VOSK_MODEL_PATH=/path/to/vosk-model

# Optional: Custom BitNet endpoint (default: http://localhost:8081/completion)
export BITNET_ENDPOINT=http://localhost:8081/completion
```

Ensure BitNet server is running:
```bash
# Start BitNet server (adjust to your BitNet setup)
bitnet-server --port 8081
```

## Usage

```bash
# Start application
./start.sh
```

## Architecture Benefits

### 1. **API Contract Adherence**
All service methods return structured results (`ProcessingResult`, `TranscriptionResult`). No mixed response types or thrown exceptions for business logic errors.

### 2. **Braun Aesthetic Implementation**
- Minimalist UI with clear hierarchy
- Black/white/gray color palette
- Purposeful spacing and typography
- No visual clutter

### 3. **Modularity & Testing**
```python
# Services can be tested independently
audio_service = AudioService(vosk_config, audio_config)
audio_service.initialize()
audio_service.start_recording()
```

### 4. **Easy Configuration**
Single source of truth in `config.py`. All hard-coded values eliminated. Environment-based configuration for deployment flexibility.

### 5. **BitNet Integration Point**
The `InferenceService` provides a clean abstraction for BitNet. Adjust the `_execute_inference` method based on actual BitNet API (CLI, Python bindings, or HTTP).

## BitNet Integration Notes

The application uses BitNet's HTTP API for text generation:

**Endpoint**: `http://localhost:8081/completion`  
**Method**: `POST`  
**Content-Type**: `application/json`

**Request format**:
```json
{
  "prompt": "Your text here",
  "n_predict": 2048,
  "temperature": 0.7,
  "stop": [],
  "stream": false
}
```

**Response parsing**: The service automatically handles multiple response formats:
- `{"content": "text"}`
- `{"text": "text"}`
- `{"completion": "text"}`
- `{"choices": [{"text": "text"}]}`

The endpoint URL can be customized via `BITNET_ENDPOINT` environment variable.

## License

MIT License - See original repository for details.

## Three Most Impactful Architectural Improvements

See ARCHITECTURE_REVIEW.md for detailed analysis.
