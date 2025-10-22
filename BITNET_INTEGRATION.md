# BitNet HTTP API Integration Guide

## Overview

The application now uses BitNet's HTTP API for local text generation. This document explains the integration details and how to verify it's working.

## API Endpoint

**Base URL**: `http://localhost:8081`  
**Completion Endpoint**: `http://localhost:8081/completion`  
**Method**: `POST`  
**Content-Type**: `application/json`

## Request Format

```json
{
  "prompt": "System prompt + user instructions + transcript text",
  "n_predict": 2048,
  "temperature": 0.7,
  "stop": [],
  "stream": false
}
```

### Parameters

- `prompt` (string, required): The full text prompt including system instructions and user transcript
- `n_predict` (integer): Maximum number of tokens to generate (default: 2048)
- `temperature` (float): Sampling temperature 0.0-2.0 (default: 0.7)
- `stop` (array): Stop sequences (default: empty)
- `stream` (boolean): Enable streaming response (default: false)

## Response Format

The service handles multiple possible response formats:

### Format 1: Simple content
```json
{
  "content": "Generated text here..."
}
```

### Format 2: Text field
```json
{
  "text": "Generated text here..."
}
```

### Format 3: Completion field
```json
{
  "completion": "Generated text here..."
}
```

### Format 4: Choices array (OpenAI-like)
```json
{
  "choices": [
    {
      "text": "Generated text here..."
    }
  ]
}
```

### Format 5: Choices with message
```json
{
  "choices": [
    {
      "message": {
        "content": "Generated text here..."
      }
    }
  ]
}
```

## Testing the Integration

### 1. Verify BitNet Server is Running

```bash
# Check if server is up
curl http://localhost:8081

# Should return something (even 404 is OK - server is responding)
```

### 2. Test Completion Endpoint

```bash
# Send a test request
curl -X POST http://localhost:8081/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Convert this to notes: I need to buy milk and eggs today.",
    "n_predict": 100,
    "temperature": 0.7,
    "stream": false
  }'
```

Expected response should contain generated text in one of the formats above.

### 3. Test from Application

1. Start the application: `./start.sh`
2. Record some speech or type in transcript area
3. Click "Generate Notes"
4. Check status messages and output

## Configuration

### Environment Variables

```bash
# Custom BitNet endpoint
export BITNET_ENDPOINT=http://localhost:8081/completion

# Or different host/port
export BITNET_ENDPOINT=http://192.168.1.100:9000/completion
```

### Code Configuration

Edit `src/core/config.py`:

```python
@dataclass(frozen=True)
class BitNetConfig:
    endpoint_url: str = "http://localhost:8081/completion"
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout_seconds: float = 30.0
```

## Error Handling

The service provides clear error messages:

### Connection Errors
```
Cannot connect to BitNet server.
Ensure BitNet is running on http://localhost:8081
```

**Solution**: Start BitNet server

### Timeout Errors
```
BitNet request timeout after 30.0s.
Ensure BitNet server is running on http://localhost:8081
```

**Solution**: 
- Check server is responsive
- Increase timeout in config
- Try simpler/shorter prompts

### HTTP Errors
```
BitNet HTTP error 500: Internal server error
```

**Solution**: Check BitNet server logs

## Customizing Response Parsing

If BitNet returns a different format, edit `_parse_response()` in `src/services/inference_service.py`:

```python
def _parse_response(self, data: dict) -> str:
    # Add your custom format
    if "your_field" in data:
        return data["your_field"].strip()
    
    # Keep existing fallbacks
    if "content" in data:
        return data["content"].strip()
    # ... etc
```

## Performance Tips

1. **Adjust timeout**: For long generations, increase `timeout_seconds` in config
2. **Token limit**: Reduce `n_predict` for faster responses
3. **Temperature**: Lower temperature (0.3-0.5) for more focused output
4. **Streaming**: Set `stream: true` for real-time output (requires code changes)

## Integration Benefits

✅ **No model files to manage** - Server handles the model  
✅ **Easy to scale** - BitNet can run on separate machine  
✅ **Clean separation** - Model inference isolated from application  
✅ **Simple debugging** - Test endpoint independently with curl  
✅ **Flexible deployment** - Change endpoint without code changes  

## Troubleshooting

### Application won't start
- Check `main.py` validation doesn't fail
- VOSK model is primary requirement
- BitNet is optional (warning shown if not available)

### "Generate Notes" button disabled
- Ensure you have recorded or typed some text
- Check console for initialization errors

### Long processing times
- Check BitNet server performance
- Try shorter transcripts
- Reduce `max_tokens` in config
- Check system resources (CPU/RAM)

### Unexpected output
- Verify response format with curl
- Check `_parse_response()` logic
- Enable debug logging
- Review system prompt in config

## Next Steps

Once integrated and tested:

1. Customize system prompt in `BitNetConfig.system_prompt`
2. Adjust generation parameters for your use case
3. Add logging for debugging
4. Consider streaming responses for better UX
5. Implement retry logic for transient failures
