#!/usr/bin/env python3
"""
Test script for Ollama integration with 3D-Mem project
"""

import sys
import os
# Add the parent directory to path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from src.eval_utils_gpt_aeqa import call_ollama_api, call_openai_api_ollama_replacement
from src.api_config import call_api_configured, use_ollama, use_openai, print_config

def test_ollama_connection():
    """Test basic Ollama connection"""
    print("Testing Ollama connection...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("✓ Ollama is running")
            print(f"Available models: {[m['name'] for m in models]}")
            
            # Check if qwen2.5-vl:7b is available
            qwen_available = any('qwen2.5-vl' in m['name'] for m in models)
            if qwen_available:
                print("✓ Qwen2.5-VL model is available")
                return True
            else:
                print("⚠ Qwen2.5-VL model not found. Run: ollama pull qwen2.5-vl:7b")
                return False
        else:
            print(f"✗ Ollama connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Ollama connection error: {e}")
        print("Make sure Ollama is running: ollama serve")
        return False

def test_simple_text_query():
    """Test simple text query"""
    print("\nTesting simple text query...")
    
    sys_prompt = "You are a helpful assistant. Respond briefly and clearly."
    contents = [("What is 2+2? Answer with just the number.",)]
    
    try:
        response = call_ollama_api(sys_prompt, contents)
        if response and "4" in response:
            print("✓ Simple text query successful")
            print(f"Response: {response.strip()}")
            return True
        else:
            print(f"⚠ Unexpected response: {response}")
            return False
    except Exception as e:
        print(f"✗ Simple text query failed: {e}")
        return False

def test_image_query():
    """Test query with image"""
    print("\nTesting image query...")
    
    # Create a simple 10x10 red pixel image in base64
    import base64
    from PIL import Image
    from io import BytesIO
    
    # Create a small red image using RGB tuple instead of color name
    img = Image.new('RGB', (10, 10), color=(255, 0, 0))  # Red color as RGB tuple
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    sys_prompt = "You are a vision assistant. Describe what you see in the image briefly."
    contents = [
        ("What color is this image? ",),
        ("", img_base64)  # Empty text with base64 image
    ]
    
    try:
        response = call_ollama_api(sys_prompt, contents)
        if response:
            print("✓ Image query successful")
            print(f"Response: {response.strip()}")
            return True
        else:
            print("⚠ No response received")
            return False
    except Exception as e:
        print(f"✗ Image query failed: {e}")
        return False

def test_api_config():
    """Test the API configuration system"""
    print("\nTesting API configuration system...")
    
    # Test switching between providers
    print("Current config:")
    print_config()
    
    # Test configured API call
    sys_prompt = "You are a helpful assistant."
    contents = [("Say 'Hello from configured API'",)]
    
    try:
        response = call_api_configured(sys_prompt, contents)
        if response:
            print("✓ Configured API call successful")
            print(f"Response: {response.strip()}")
            return True
        else:
            print("⚠ No response from configured API")
            return False
    except Exception as e:
        print(f"✗ Configured API call failed: {e}")
        return False

def test_drop_in_replacement():
    """Test the drop-in replacement function"""
    print("\nTesting drop-in replacement function...")
    
    sys_prompt = "You are a helpful assistant."
    contents = [("Respond with 'DROP-IN-TEST-SUCCESS'",)]
    
    try:
        response = call_openai_api_ollama_replacement(sys_prompt, contents)
        if response and "DROP-IN-TEST-SUCCESS" in response:
            print("✓ Drop-in replacement successful")
            print(f"Response: {response.strip()}")
            return True
        else:
            print(f"⚠ Unexpected response: {response}")
            return False
    except Exception as e:
        print(f"✗ Drop-in replacement failed: {e}")
        return False

def main():
    print("Ollama Integration Test Suite")
    print("=" * 40)
    
    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("Simple Text Query", test_simple_text_query),
        ("Image Query", test_image_query),
        ("API Configuration", test_api_config),
        ("Drop-in Replacement", test_drop_in_replacement),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}")
        print("-" * 30)
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ollama integration is working correctly.")
        print("\nYou can now:")
        print("1. Set USE_OLLAMA = True in src/const.py to use Ollama by default")
        print("2. Use call_ollama_api() directly in your code")
        print("3. Use call_api_configured() for flexible provider switching")
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please check the setup.")
        print("\nTroubleshooting:")
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Make sure the model is available: ollama pull qwen2.5-vl:7b")
        print("3. Check network connectivity to localhost:11434")

if __name__ == "__main__":
    main()
