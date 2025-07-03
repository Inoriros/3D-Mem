import os

# Try to load environment variables from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("Note: python-dotenv not installed. Using system environment variables only.")
    print("To use .env files, install with: pip install python-dotenv")
except Exception:
    pass  # .env file not found or other error, continue with system env vars

# about habitat scene
INVALID_SCENE_ID = []

# about chatgpt api - SECURE: Using environment variables
END_POINT = os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_KEY:
    print("WARNING: OPENAI_API_KEY not found in environment variables!")
    print("Please set the OPENAI_API_KEY environment variable or create a .env file.")

# Ollama configuration - SECURE: Using environment variables with defaults
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434") 
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5vl:72b")
