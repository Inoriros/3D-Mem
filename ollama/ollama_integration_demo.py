#!/usr/bin/env python3
"""
Demo script showing how to use the new Ollama functions as replacements for OpenAI API calls.

This script demonstrates three ways to switch from OpenAI to Ollama:
1. Simple function replacement
2. Using the new Ollama functions directly
3. Global function aliasing

Before running this, make sure:
1. Ollama is installed and running: curl -fsSL https://ollama.com/install.sh | sh
2. Qwen2.5-VL model is pulled: ollama pull qwen2.5-vl:7b
3. Ollama server is running: ollama serve (if not already running as a service)
"""

import sys
import os
# Add the parent directory to path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.eval_utils_gpt_aeqa import call_openai_api, call_ollama_api, call_openai_api_ollama_replacement

def demo_ollama_usage():
    """Demonstrate different ways to use Ollama instead of OpenAI"""
    
    # Example input (text only)
    sys_prompt = "You are a helpful assistant that answers questions clearly and concisely."
    contents = [("What is the capital of France?",)]
    
    print("=== Demo: Text-only query ===")
    print(f"System prompt: {sys_prompt}")
    print(f"User input: {contents[0][0]}")
    print()
    
    # Method 1: Direct Ollama call
    print("Method 1: Using call_ollama_api directly")
    try:
        response1 = call_ollama_api(sys_prompt, contents)
        print(f"Response: {response1}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # Method 2: Drop-in replacement function
    print("Method 2: Using drop-in replacement function")
    try:
        response2 = call_openai_api_ollama_replacement(sys_prompt, contents)
        print(f"Response: {response2}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # Example with image (base64 encoded)
    print("=== Demo: Text + Image query ===")
    print("Note: This would work with actual base64 encoded images")
    contents_with_image = [
        ("Describe what you see in this image: ",),
        ("A sample base64 image would go here", "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
    ]
    
    try:
        response3 = call_ollama_api(sys_prompt, contents_with_image)
        print(f"Response: {response3}")
    except Exception as e:
        print(f"Error: {e}")

def show_replacement_instructions():
    """Show how to replace OpenAI calls in the existing codebase"""
    
    print("=== Replacement Instructions ===")
    print()
    print("To switch from OpenAI to Ollama in your existing code, you have several options:")
    print()
    
    print("Option 1: Global function replacement (recommended for testing)")
    print("Add this line after imports in your main script:")
    print("from src.eval_utils_gpt_aeqa import call_ollama_api as call_openai_api")
    print()
    
    print("Option 2: Use the drop-in replacement function")
    print("Replace calls like:")
    print("  response = call_openai_api(sys_prompt, contents)")
    print("With:")
    print("  response = call_openai_api_ollama_replacement(sys_prompt, contents)")
    print()
    
    print("Option 3: Direct function calls")
    print("Replace calls like:")
    print("  response = call_openai_api(sys_prompt, contents)")
    print("With:")
    print("  response = call_ollama_api(sys_prompt, contents)")
    print()
    
    print("Option 4: Modify the original function")
    print("In both eval_utils_gpt_aeqa.py and eval_utils_gpt_goatbench.py, replace the content of")
    print("call_openai_api() with a call to call_ollama_api()")
    print()

def show_setup_instructions():
    """Show setup instructions for Ollama"""
    
    print("=== Setup Instructions ===")
    print()
    print("1. Install Ollama:")
    print("   curl -fsSL https://ollama.com/install.sh | sh")
    print()
    print("2. Pull the Qwen2.5-VL model:")
    print("   ollama pull qwen2.5-vl:7b")
    print()
    print("3. Start Ollama server (if not running as service):")
    print("   ollama serve")
    print()
    print("4. Verify the model is available:")
    print("   ollama list")
    print()
    print("5. Test the setup:")
    print("   curl http://localhost:11434/api/generate -d '{")
    print('     "model": "qwen2.5-vl:7b",')
    print('     "prompt": "Hello, how are you?",')
    print('     "stream": false')
    print("   }'")
    print()

if __name__ == "__main__":
    print("Ollama Integration Demo")
    print("=" * 50)
    print()
    
    show_setup_instructions()
    show_replacement_instructions()
    
    # Only run the demo if user confirms Ollama is set up
    try:
        user_input = input("Do you want to run the demo? (Requires Ollama to be running) [y/N]: ")
        if user_input.lower() in ['y', 'yes']:
            demo_ollama_usage()
        else:
            print("Demo skipped. Set up Ollama first, then run the demo.")
            print("\nTo set up Ollama:")
            print("1. Run: ./setup_ollama.sh")
            print("2. Or manually: ollama pull qwen2.5-vl:7b && ollama serve")
            print("3. Then run this demo again")
    except KeyboardInterrupt:
        print("\nDemo cancelled.")
