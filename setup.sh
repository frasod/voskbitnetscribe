#!/bin/bash
# Setup script for Linux
# Clean, reproducible environment setup

set -e

echo "=== VOSK BitNet Scribe Setup ==="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Download VOSK model: https://alphacephei.com/vosk/models"
echo "   Recommended: vosk-model-small-en-us-0.15"
echo "2. Extract to project directory"
echo "3. Set BITNET_MODEL_PATH environment variable"
echo "4. Run: ./start.sh"
echo ""
