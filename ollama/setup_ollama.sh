#!/bin/bash

# Ollama Setup Script for 3D-Mem Project
# This script sets up Ollama and the Qwen2.5-VL model for use as a replacement to OpenAI API

set -e  # Exit on any error

echo "=================================="
echo "Ollama Setup for 3D-Mem Project"
echo "=================================="
echo

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
    echo "✓ Ollama is already installed"
    ollama --version
else
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "✓ Ollama installed successfully"
fi

echo

# Check if Ollama service is running
if pgrep -x "ollama" > /dev/null; then
    echo "✓ Ollama service is running"
else
    echo "Starting Ollama service..."
    # Try to start ollama serve in background
    ollama serve &
    OLLAMA_PID=$!
    echo "✓ Ollama service started (PID: $OLLAMA_PID)"
    sleep 5  # Give it time to start
fi

echo

# Check if the model is already available
if ollama list | grep -q "qwen2.5-vl:7b"; then
    echo "✓ Qwen2.5-VL:7b model is already available"
else
    echo "Pulling Qwen2.5-VL:7b model (this may take a while)..."
    ollama pull qwen2.5-vl:7b
    echo "✓ Qwen2.5-VL:7b model pulled successfully"
fi

echo

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements_ollama.txt
echo "✓ Python dependencies installed"

echo

# Test the setup
echo "Testing Ollama API..."
response=$(curl -s -X POST http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{
        "model": "qwen2.5-vl:7b",
        "prompt": "Hello! Please respond with just the word SUCCESS if you can see this message.",
        "stream": false
    }' | python3 -c "import sys, json; print(json.load(sys.stdin).get('response', 'ERROR'))")

if [[ "$response" == *"SUCCESS"* ]]; then
    echo "✓ Ollama API test successful"
else
    echo "⚠ Ollama API test failed. Response: $response"
    echo "Please check if Ollama is running: ollama serve"
fi

echo

# Show available models
echo "Available models:"
ollama list

echo
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo
echo "Next steps:"
echo "1. To use Ollama instead of OpenAI, set USE_OLLAMA = True in src/const.py"
echo "2. Or use the new functions directly:"
echo "   - call_ollama_api(sys_prompt, contents)"
echo "   - call_openai_api_ollama_replacement(sys_prompt, contents)"
echo "   - call_api_smart(sys_prompt, contents)  # Auto-chooses based on config"
echo
echo "3. Run the demo: python ollama/ollama_integration_demo.py"
echo
echo "Ollama server URL: http://localhost:11434"
echo "Model: qwen2.5-vl:7b"
echo
