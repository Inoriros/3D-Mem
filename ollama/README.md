# Ollama Integration Files

This folder contains all the files needed for integrating Ollama with the 3D-Mem project.

## Files in this folder:

### Setup and Testing
- `setup_ollama.sh` - Automated setup script for Ollama
- `test_ollama_integration.py` - Comprehensive test suite
- `quick_test.py` - Quick test for basic functionality
- `requirements_ollama.txt` - Python dependencies

### Integration Tools
- `patch_for_ollama.py` - Auto-patcher to update existing code
- `ollama_integration_demo.py` - Demo and usage examples
- `ollama_summary.py` - Summary of all integration options

### Documentation
- `OLLAMA_INTEGRATION.md` - Comprehensive documentation
- `README.md` - This file

## Quick Start

From the main project directory (3D-Mem/):

1. **Setup Ollama:**
   ```bash
   cd ollama/
   ./setup_ollama.sh
   ```

2. **Test the integration:**
   ```bash
   python test_ollama_integration.py
   ```

3. **Run the demo:**
   ```bash
   python ollama_integration_demo.py
   ```

4. **Patch your existing code (optional):**
   ```bash
   python patch_for_ollama.py
   ```

## Important Notes

- All scripts in this folder should be run from within the `ollama/` directory
- The scripts automatically adjust the Python path to import from the parent `src/` directory
- Make sure Ollama is installed and running before testing

## Troubleshooting

If you get import errors:
1. Make sure you're running scripts from the `ollama/` directory
2. Check that the `src/` directory exists in the parent folder
3. Verify all required dependencies are installed

If you get the "*c* argument looks like a single numeric RGB or RGBA sequence" warning:
- This has been fixed in the updated test files
- The warning was related to PIL image creation and is now resolved

For more detailed troubleshooting, see `OLLAMA_INTEGRATION.md`.
