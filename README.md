# VOSK BitNet Scribe

A clean, modular speech-to-text and chat application combining VOSK speech recognition with local BitNet inference. Features both voice transcription and text-based chat in a minimalist interface.

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
- **BitNet/LLM server running separately** (see Setup below)
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

### Setting Up the LLM Server

**IMPORTANT**: This application requires a separate LLM inference server running. Choose one option:

#### Option 1: Ollama (Recommended - Easiest)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve

# Pull a model
ollama pull llama3.2

# Configure app to use Ollama:
# In Settings tab, set endpoint to: http://localhost:11434/api/generate
```

#### Option 2: llama.cpp
```bash
# Clone and build
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Download a model (GGUF format)
# Example: https://huggingface.co/models

# Start server on port 8081
./server -m /path/to/model.gguf --port 8081
```

#### Option 3: LM Studio
- Download from https://lmstudio.ai/
- Start local server (usually port 1234)
- In app Settings, set endpoint to: `http://localhost:1234/v1/completions`

#### Option 4: BitNet (Original)
```bash
# Start BitNet server on port 8081
bitnet-server --port 8081
```

**The app will NOT work without one of these servers running!**

### Configuration

Set environment variables (optional):

```bash
# Optional: Custom VOSK model location
export VOSK_MODEL_PATH=/path/to/vosk-model

# Optional: Custom BitNet endpoint (default: http://localhost:8081/completion)
export BITNET_ENDPOINT=http://localhost:8081/completion
```

**Or configure in the app:**
1. Open the application
2. Go to the **Settings** tab
3. Update the **Endpoint URL** to match your LLM server
4. Click **Apply Settings**

## Usage

```bash
# Start application
./start.sh
```

The application features two main modes:

### Voice Transcription
1. Click "Start Recording" to capture speech
2. Speak into your microphone
3. Click "Stop Recording" to end capture
4. Click "Generate Notes" to process transcript with BitNet
5. Click "Copy to Clipboard" to save results

### Chat Mode
1. Click the "Chat" tab at the top
2. Type your message in the input field
3. Press Enter or click "Send"
4. The AI assistant responds with context from conversation history
5. Use "Clear History" to start a fresh conversation

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
