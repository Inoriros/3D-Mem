#!/bin/bash

# Setup script for H200 machine with Ollama and qwen2.5vl:72b (NO SUDO REQUIRED)
# Run this script on your H200 machine

echo "Setting up Ollama on H200 machine (user-space installation)..."

# Install Ollama in user space (no sudo required)
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama to ~/.local/bin (no sudo required)..."
    
    # Create local bin directory if it doesn't exist
    mkdir -p ~/.local/bin
    
    # Download and install Ollama binary to user space
    curl -L https://ollama.ai/download/ollama-linux-amd64 -o ~/.local/bin/ollama
    chmod +x ~/.local/bin/ollama
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    echo "Ollama installed to ~/.local/bin/ollama"
    echo "Added ~/.local/bin to PATH"
else
    echo "Ollama is already installed"
fi

# Make sure we can find ollama
export PATH="$HOME/.local/bin:$PATH"

# Pull the qwen2.5vl:72b model (this will take some time)
echo "Pulling qwen2.5vl:72b model (this may take 30+ minutes)..."
ollama pull qwen2.5vl:72b

# Start Ollama server with proper host binding (allows external connections)
echo "Starting Ollama server..."
OLLAMA_HOST=0.0.0.0:11434 ollama serve &

# Wait a moment for server to start
sleep 5

# Test if the model is working
echo "Testing the model..."
ollama run qwen2.5vl:72b "Hello, can you see this message?"

echo ""
echo "Setup complete!"
echo "Ollama server is running on port 11434"
echo "Model qwen2.5vl:72b is ready"
echo ""
echo "To keep the server running, you can use:"
echo "  nohup env OLLAMA_HOST=0.0.0.0:11434 ollama serve > ollama.log 2>&1 &"
echo ""
echo "Don't forget to:"
echo "1. Update the IP address in your local const.py file"
echo "2. Make sure port 11434 is accessible from your local machine"
