# Quick Setup Instructions for H200 (No Sudo Required)

## Summary
You want to run qwen2.5vl:72b on your H200 machine at `sairpro.cse.buffalo.edu` and use it from your local desktop without needing sudo permissions.

## Step 1: Copy Scripts to H200
```bash
# From your local machine
scp setup_h200_ollama.sh manual_install_h200.sh your_username@sairpro.cse.buffalo.edu:~/
```

## Step 2: SSH to H200 and Install
```bash
# SSH to H200
ssh your_username@sairpro.cse.buffalo.edu

# Try the automatic installer first
chmod +x setup_h200_ollama.sh
./setup_h200_ollama.sh

# If that fails, use manual installer
chmod +x manual_install_h200.sh
./manual_install_h200.sh
```

## Step 3: Pull Model and Start Server
```bash
# On H200 machine
~/.local/bin/ollama pull qwen2.5vl:72b  # Takes 30+ minutes

# Start server (accessible from network)
OLLAMA_HOST=0.0.0.0:11434 ~/.local/bin/ollama serve
```

## Step 4: Keep Server Running (Background)
```bash
# On H200 machine - run in background
nohup env OLLAMA_HOST=0.0.0.0:11434 ~/.local/bin/ollama serve > ollama.log 2>&1 &

# You can now logout and the server will keep running
```

## Step 5: Test from Local Machine
```bash
# From your local desktop
python test_h200_connection.py

# If all tests pass, run your evaluations
python run_aeqa_evaluation.py
```

## Troubleshooting
If connection fails:
1. Check if server is running: `ps aux | grep ollama`
2. Check if port is accessible: `netstat -tlnp | grep 11434`
3. Test basic connectivity: `curl http://sairpro.cse.buffalo.edu:11434/api/tags`

## Configuration Already Done
- ✅ `src/const.py` is already configured with the correct server URL
- ✅ `USE_OLLAMA = True` is set
- ✅ `OLLAMA_MODEL = "qwen2.5vl:72b"` is configured

You're all set! Just run the setup on H200 and test the connection.
