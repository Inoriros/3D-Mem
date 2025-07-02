#!/usr/bin/env python3
"""
Quick test to check if the PIL image creation issue is resolved
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_image_creation():
    """Test creating an image without matplotlib warnings"""
    print("Testing image creation...")
    
    try:
        import base64
        from PIL import Image
        from io import BytesIO
        
        # Create a small red image using RGB tuple
        print("Creating 10x10 red image...")
        img = Image.new('RGB', (10, 10), color=(255, 0, 0))
        
        # Convert to base64
        print("Converting to base64...")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        print(f"✓ Image created successfully! Base64 length: {len(img_base64)}")
        print(f"First 50 characters: {img_base64[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating image: {e}")
        return False

def test_imports():
    """Test importing the required modules"""
    print("Testing module imports...")
    
    try:
        from src.eval_utils_gpt_aeqa import call_ollama_api
        print("✓ Successfully imported call_ollama_api")
        
        from src.api_config import call_api_configured
        print("✓ Successfully imported call_api_configured")
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        print("Make sure you're running from the ollama/ directory")
        return False

if __name__ == "__main__":
    print("Quick Ollama Integration Test")
    print("=" * 40)
    
    success1 = test_imports()
    print()
    success2 = test_image_creation()
    
    print("\n" + "=" * 40)
    if success1 and success2:
        print("✓ All quick tests passed!")
        print("You can now run the full test: python test_ollama_integration.py")
    else:
        print("⚠ Some tests failed. Check the errors above.")
