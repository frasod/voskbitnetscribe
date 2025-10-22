#!/bin/bash
# Start script for Linux

set -e

# Activate virtual environment
source venv/bin/activate

# Set default VOSK model path if not set
export VOSK_MODEL_PATH="${VOSK_MODEL_PATH:-$(pwd)/vosk-model-small-en-us-0.15}"

# Set default BitNet endpoint if not set
export BITNET_ENDPOINT="${BITNET_ENDPOINT:-http://localhost:8081/completion}"

# Check if BitNet server is reachable
echo "Checking BitNet server..."
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:8081 | grep -q "200\|404"; then
    echo "Warning: Cannot connect to BitNet server at http://localhost:8081"
    echo "Please ensure BitNet server is running before using text processing features."
    echo ""
fi

# Start application
echo "Starting VOSK BitNet Scribe..."
python main.py
