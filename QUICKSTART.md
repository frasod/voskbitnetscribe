# QUICKSTART GUIDE

## Prerequisites Check

```bash
# 1. Python 3.8+
python3 --version

# 2. Audio device (microphone)
arecord -l  # List audio devices

# 3. BitNet server running
curl http://localhost:8081
# Should get a response (even 404 is OK - server is up)
```

## Installation (5 minutes)

```bash
# 1. Setup environment
./setup.sh

# 2. Download VOSK model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip

# 3. Start BitNet server (in separate terminal)
# Adjust command based on your BitNet installation
bitnet-server --port 8081

# 4. Run application
./start.sh
```

## Usage Flow

```
1. Click "Start Recording"
2. Speak into microphone
3. Click "Stop Recording"
4. [Optional] Add custom processing instructions
5. Click "Generate Notes"
6. Review output
7. Click "Copy to Clipboard"
```

## Customization

### Custom Processing Prompt
In the "Processing Instructions" field, enter:
```
Summarize this transcript into bullet points focusing on action items.
```

### Different VOSK Model
```bash
export VOSK_MODEL_PATH=/path/to/different/model
```

### BitNet Configuration
Edit `src/core/config.py` → `BitNetConfig` class:
```python
endpoint_url: str = "http://localhost:8081/completion"  # Change endpoint
max_tokens: int = 4096  # Increase token limit
temperature: float = 0.5  # More deterministic
```

Or use environment variable:
```bash
export BITNET_ENDPOINT=http://your-server:port/completion
```

## Troubleshooting

### "VOSK model not found"
```bash
# Check path
echo $VOSK_MODEL_PATH
ls -la $VOSK_MODEL_PATH

# Should contain: am/, conf/, graph/, ivector/
```

### "BitNet CLI not found"
```bash
# Check BitNet server status
curl http://localhost:8081

# If not running, start BitNet server
bitnet-server --port 8081

# Check if server is responding
curl -X POST http://localhost:8081/completion \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","n_predict":10}'
```

### "No audio device"
```bash
# Check microphone
arecord -l

# Test recording
arecord -d 5 test.wav
aplay test.wav
```

## Development

### Run Tests
```bash
source venv/bin/activate
pytest tests/
```

### Modify BitNet Integration
Edit `src/services/inference_service.py`:
- Change endpoint in `BitNetConfig`
- Adjust request payload format in `_execute_inference()`
- Modify response parsing in `_parse_response()`

### Change UI Theme
Edit `src/ui/styles.py`:
```python
# Change colors in UIConfig
background: str = "#YOUR_COLOR"
primary: str = "#YOUR_COLOR"
```

## Architecture Overview

See `ARCHITECTURE_REVIEW.md` for detailed analysis.

**Key files**:
- `main.py` - Entry point
- `src/core/config.py` - All configuration
- `src/services/audio_service.py` - VOSK integration
- `src/services/inference_service.py` - BitNet integration
- `src/ui/main_window.py` - User interface

## Next Steps

1. **Read** `ARCHITECTURE_REVIEW.md` for design decisions
2. **Run** `python3 architecture_diagram.py` to see structure
3. **Explore** modular service layer for customization
4. **Test** with your specific BitNet model

## Support

This is a clean, well-documented codebase following industry best practices. All code is self-documenting with clear types and contracts.
