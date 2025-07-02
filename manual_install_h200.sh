#!/bin/bash

# Manual Ollama installation script for H200 (NO SUDO, NO NETWORK RESTRICTIONS)
# Use this if the main setup script fails due to network restrictions

echo "Manual Ollama installation for H200 machine..."

# Method 1: Direct binary download
echo "Method 1: Downloading Ollama binary..."
mkdir -p ~/.local/bin

# Try different download methods
if command -v wget &> /dev/null; then
    echo "Using wget to download..."
    wget -O ~/.local/bin/ollama https://ollama.ai/download/ollama-linux-amd64
elif command -v curl &> /dev/null; then
    echo "Using curl to download..."
    curl -L https://ollama.ai/download/ollama-linux-amd64 -o ~/.local/bin/ollama
else
    echo "Neither wget nor curl available. Please manually download:"
    echo "1. Go to: https://ollama.ai/download/ollama-linux-amd64"
    echo "2. Save the file as: ~/.local/bin/ollama"
    echo "3. Run: chmod +x ~/.local/bin/ollama"
    exit 1
fi

# Make executable
chmod +x ~/.local/bin/ollama

# Add to PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "Added ~/.local/bin to PATH in ~/.bashrc"
fi

export PATH="$HOME/.local/bin:$PATH"

# Verify installation
if ~/.local/bin/ollama --version; then
    echo "✅ Ollama installed successfully!"
else
    echo "❌ Ollama installation failed"
    exit 1
fi

# Create Ollama data directory
mkdir -p ~/.ollama

echo ""
echo "Installation complete!"
echo "You can now run:"
echo "  ~/.local/bin/ollama pull qwen2.5vl:72b"
echo "  OLLAMA_HOST=0.0.0.0:11434 ~/.local/bin/ollama serve"
