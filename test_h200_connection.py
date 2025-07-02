#!/usr/bin/env python3

"""
Test script to verify Ollama connection to remote H200 machine
Run this script from your local desktop after setting up the H200 machine
"""

import requests
import json
import time
from src.const import OLLAMA_URL, OLLAMA_MODEL, USE_OLLAMA

def test_ollama_connection():
    """Test basic connection to Ollama server"""
    print(f"Testing connection to: {OLLAMA_URL}")
    print(f"Model: {OLLAMA_MODEL}")
    print(f"USE_OLLAMA: {USE_OLLAMA}")
    print("-" * 50)
    
    try:
        # Test server availability
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json()
            print("✅ Server is accessible")
            print("Available models:")
            for model in models.get('models', []):
                print(f"  - {model['name']}")
            
            # Check if our target model is available
            model_names = [m['name'] for m in models.get('models', [])]
            if OLLAMA_MODEL in model_names:
                print(f"✅ Target model {OLLAMA_MODEL} is available")
            else:
                print(f"❌ Target model {OLLAMA_MODEL} is NOT available")
                print("You may need to pull it with: ollama pull qwen2.5vl:72b")
                return False
        else:
            print(f"❌ Server responded with status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print("Please check:")
        print("1. H200 machine is accessible from your network")
        print("2. Ollama server is running on H200 machine")
        print("3. Port 11434 is open/accessible")
        print("4. IP address in const.py is correct")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def test_simple_inference():
    """Test simple text inference"""
    print("\nTesting simple text inference...")
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": "Hello! Please respond with 'Connection successful' if you can see this message.",
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 50,
        }
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Text inference successful")
            print(f"Response: {result.get('response', 'No response')}")
            return True
        else:
            print(f"❌ Inference failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Inference error: {e}")
        return False

def test_chat_format():
    """Test chat format (same as used in the codebase)"""
    print("\nTesting chat format...")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Please say 'Chat format working' to confirm the connection."},
    ]
    
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 50,
        }
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat format successful")
            print(f"Response: {result.get('message', {}).get('content', 'No response')}")
            return True
        else:
            print(f"❌ Chat failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

def main():
    print("🧪 Testing Ollama connection to H200 machine")
    print("=" * 60)
    
    if not test_ollama_connection():
        print("\n❌ Basic connection test failed. Please fix connection issues first.")
        return
    
    if not test_simple_inference():
        print("\n❌ Simple inference test failed.")
        return
    
    if not test_chat_format():
        print("\n❌ Chat format test failed.")
        return
    
    print("\n🎉 All tests passed! Your H200 Ollama setup is working correctly.")
    print("\nYou can now run your evaluations with:")
    print("  python run_aeqa_evaluation.py")
    print("  python run_goatbench_evaluation.py")

if __name__ == "__main__":
    main()
