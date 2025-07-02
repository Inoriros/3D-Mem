# H200 Remote Ollama Setup Guide

This guide helps you set up Ollama with qwen2.5vl:72b on a remote H200 machine and configure your local desktop to use it for inference.

## Prerequisites

- SSH access to an H200 machine
- The H200 machine should have sufficient VRAM (72B model needs ~40GB+ VRAM)
- Network connectivity between your local machine and H200 machine
- Port 11434 should be accessible from your local machine to the H200 machine

## Step 1: Setup on H200 Machine (No Sudo Required)

1. SSH into your H200 machine:
   ```bash
   ssh user@sairpro.cse.buffalo.edu
   ```

2. Copy the setup script to the H200 machine:
   ```bash
   # On your local machine, copy the setup script
   scp setup_h200_ollama.sh user@sairpro.cse.buffalo.edu:~/
   ```

3. Run the setup script on H200:
   ```bash
   # On H200 machine
   chmod +x setup_h200_ollama.sh
   ./setup_h200_ollama.sh
   ```

   This will:
   - Install Ollama to ~/.local/bin (no sudo required)
   - Add ~/.local/bin to your PATH
   - Pull the qwen2.5vl:72b model (takes 30+ minutes)
   - Start the Ollama server

4. If the automatic script fails, use the manual installation:
   ```bash
   # Alternative: manual installation
   scp manual_install_h200.sh user@sairpro.cse.buffalo.edu:~/
   chmod +x manual_install_h200.sh
   ./manual_install_h200.sh
   
   # Then manually pull the model and start server
   ~/.local/bin/ollama pull qwen2.5vl:72b
   OLLAMA_HOST=0.0.0.0:11434 ~/.local/bin/ollama serve
   ```

5. Keep the server running persistently:
   ```bash
   # On H200 machine - run in background
   nohup env OLLAMA_HOST=0.0.0.0:11434 ~/.local/bin/ollama serve > ollama.log 2>&1 &
   ```

## Step 2: Configure Local Desktop

1. Update the IP address in `src/const.py`:
   ```python
   OLLAMA_URL = "http://sairpro.cse.buffalo.edu:11434"  # Already updated for you
   ```

2. Verify the configuration is correct:
   ```bash
   # Check the current settings
   grep -A 3 "Ollama configuration" src/const.py
   ```

## Step 3: Test the Connection

1. Run the test script:
   ```bash
   python test_h200_connection.py
   ```

   This will test:
   - Server connectivity
   - Model availability
   - Simple inference
   - Chat format compatibility

## Step 4: Troubleshooting

### Common Issues:

1. **Connection Refused**
   - Check if Ollama server is running on H200: `ps aux | grep ollama`
   - Verify the server is bound to 0.0.0.0: `netstat -tlnp | grep 11434`
   - Check firewall settings on H200 machine

2. **Model Not Found**
   - Pull the model: `~/.local/bin/ollama pull qwen2.5vl:72b`
   - List available models: `~/.local/bin/ollama list`

3. **Timeout Issues**
   - The 72B model is large and may take longer to respond
   - Check H200 VRAM usage: `nvidia-smi`
   - Increase timeout in test script if needed

4. **Network Issues**
   - Test basic connectivity: `telnet your_h200_ip 11434`
   - Check if port 11434 is accessible from your network
   - Verify IP address is correct in const.py

### Useful Commands:

On H200 machine:
```bash
# Check Ollama status (user-space installation)
~/.local/bin/ollama list
ps aux | grep ollama

# Check GPU usage
nvidia-smi

# View Ollama logs
tail -f ollama.log

# Restart Ollama server (user-space)
pkill ollama
OLLAMA_HOST=0.0.0.0:11434 ~/.local/bin/ollama serve
```

On local machine:
```bash
# Test basic connectivity
curl http://sairpro.cse.buffalo.edu:11434/api/tags

# Run evaluations
python run_aeqa_evaluation.py
python run_goatbench_evaluation.py
```

## Performance Notes

- qwen2.5vl:72b is significantly larger and more capable than the 7b version
- Inference will be slower but quality should be much better
- Make sure H200 has sufficient VRAM (recommend 80GB+ for optimal performance)
- Consider adjusting timeout values in eval scripts if inference takes longer

## Security Considerations

- Ollama server will be accessible from network - ensure proper firewall rules
- Consider using SSH tunneling for additional security:
  ```bash
  ssh -L 11434:localhost:11434 user@your_h200_ip
  # Then use OLLAMA_URL = "http://localhost:11434" in const.py
  ```
