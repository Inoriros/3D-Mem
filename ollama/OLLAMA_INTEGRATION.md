# Ollama Integration for 3D-Mem Project

This integration allows you to replace OpenAI API calls with local Ollama models, specifically using the Qwen2.5-VL:7b model for vision-language tasks.

## Quick Start

### 1. Setup Ollama

Run the automated setup script:

```bash
./setup_ollama.sh
```

Or manually:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull qwen2.5-vl:7b

# Start the server (if not running as service)
ollama serve
```

### 2. Install Python Dependencies

```bash
pip install -r requirements_ollama.txt
```

### 3. Test the Integration

```bash
python test_ollama_integration.py
```

### 4. Use in Your Code

#### Option A: Configuration-based switching

```python
# In src/const.py, set:
USE_OLLAMA = True

# Then use the smart API function:
from src.eval_utils_gpt_aeqa import call_api_smart
response = call_api_smart(sys_prompt, contents)
```

#### Option B: Direct function replacement

```python
# Replace this:
from src.eval_utils_gpt_aeqa import call_openai_api
response = call_openai_api(sys_prompt, contents)

# With this:
from src.eval_utils_gpt_aeqa import call_ollama_api
response = call_ollama_api(sys_prompt, contents)
```

#### Option C: Drop-in replacement function

```python
# Replace this:
response = call_openai_api(sys_prompt, contents)

# With this:
response = call_openai_api_ollama_replacement(sys_prompt, contents)
```

#### Option D: Advanced configuration

```python
from src.api_config import use_ollama, call_api_configured

# Switch to Ollama
use_ollama()

# Make calls
response = call_api_configured(sys_prompt, contents)
```

## Available Functions

### Core Functions

- `call_ollama_api(sys_prompt, contents, model="qwen2.5-vl:7b", ollama_url="http://localhost:11434")` - Direct Ollama API call
- `call_openai_api_ollama_replacement(sys_prompt, contents)` - Drop-in replacement for `call_openai_api`
- `call_api_smart(sys_prompt, contents)` - Automatically chooses provider based on `USE_OLLAMA` setting

### Configuration Functions

- `call_api_configured(sys_prompt, contents)` - Uses advanced configuration system
- `use_ollama(model=None, url=None)` - Switch to Ollama provider
- `use_openai(endpoint=None, api_key=None)` - Switch to OpenAI provider
- `print_config()` - Show current configuration

## Input Format

The functions maintain the same input format as the original OpenAI functions:

```python
# System prompt
sys_prompt = "You are a helpful assistant..."

# Contents: list of tuples (text, optional_base64_image)
contents = [
    ("What do you see in this image?",),
    ("", base64_encoded_image_string)
]

response = call_ollama_api(sys_prompt, contents)
```

## Configuration Options

### Environment Variables

You can override settings using environment variables:

```bash
export USE_OLLAMA=true
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=qwen2.5-vl:7b
```

### Configuration File

Update `src/const.py`:

```python
USE_OLLAMA = True  # Set to True to use Ollama instead of OpenAI
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5-vl:7b"
```

## Model Information

- **Model**: Qwen2.5-VL:7b
- **Capabilities**: Vision-language understanding, text generation
- **Size**: ~7 billion parameters
- **Vision**: Supports image understanding tasks
- **Local**: Runs completely offline once downloaded

## Performance Considerations

- **First call**: May be slower due to model loading
- **Subsequent calls**: Faster as model stays in memory
- **Memory usage**: ~8-16GB RAM depending on system
- **GPU**: Will use GPU if available (recommended)

## Troubleshooting

### Ollama Not Running

```bash
# Check if running
pgrep ollama

# Start manually
ollama serve

# Check status
curl http://localhost:11434/api/tags
```

### Model Not Available

```bash
# List models
ollama list

# Pull model if missing
ollama pull qwen2.5-vl:7b
```

### Connection Issues

```bash
# Test API
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5-vl:7b", "prompt": "Hello", "stream": false}'
```

### Memory Issues

If you encounter out-of-memory errors:

1. Close other applications
2. Use a smaller model: `ollama pull qwen2.5-vl:1.5b` (if available)
3. Increase system swap space
4. Use GPU if available

## Files Modified

- `src/eval_utils_gpt_aeqa.py` - Added Ollama functions
- `src/eval_utils_gpt_goatbench.py` - Added Ollama functions  
- `src/const.py` - Added Ollama configuration
- `src/api_config.py` - New advanced configuration module

## Files Added

- `ollama_integration_demo.py` - Demo and usage examples
- `test_ollama_integration.py` - Comprehensive test suite
- `setup_ollama.sh` - Automated setup script
- `requirements_ollama.txt` - Python dependencies
- `OLLAMA_INTEGRATION.md` - This documentation

## Usage in Evaluation Scripts

To use Ollama in the existing evaluation scripts:

### For AEQA Evaluation

Edit the calls in `src/eval_utils_gpt_aeqa.py`:

```python
# Replace line 272 and 342:
# response = call_openai_api(prefiltering_sys, prefiltering_content)
response = call_ollama_api(prefiltering_sys, prefiltering_content)

# full_response = call_openai_api(sys_prompt, content)  
full_response = call_ollama_api(sys_prompt, content)
```

### For GoatBench Evaluation

Edit the calls in `src/eval_utils_gpt_goatbench.py` similarly.

### Or Use Global Configuration

Set `USE_OLLAMA = True` in `src/const.py` and replace all `call_openai_api` calls with `call_api_smart`.

## Next Steps

1. Run the test suite to verify everything works
2. Update your evaluation scripts to use the new functions
3. Compare results between OpenAI and Ollama models
4. Optimize prompts if needed for the local model

For questions or issues, check the troubleshooting section or test with the provided test script.
