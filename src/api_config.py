"""
Advanced API configuration module for 3D-Mem project.
Provides flexible switching between OpenAI and Ollama APIs.
"""

import os
from typing import Optional, Dict, Any
from src.const import USE_OLLAMA, OLLAMA_URL, OLLAMA_MODEL, END_POINT, OPENAI_KEY

class APIConfig:
    """Configuration manager for API providers"""
    
    def __init__(self):
        self.use_ollama = USE_OLLAMA
        self.ollama_url = OLLAMA_URL
        self.ollama_model = OLLAMA_MODEL
        self.openai_endpoint = END_POINT
        self.openai_key = OPENAI_KEY
        
        # Allow environment variable overrides
        self.use_ollama = os.getenv('USE_OLLAMA', str(self.use_ollama)).lower() == 'true'
        self.ollama_url = os.getenv('OLLAMA_URL', self.ollama_url)
        self.ollama_model = os.getenv('OLLAMA_MODEL', self.ollama_model)
        self.openai_endpoint = os.getenv('OPENAI_ENDPOINT', self.openai_endpoint)
        self.openai_key = os.getenv('OPENAI_KEY', self.openai_key)
    
    def get_provider(self) -> str:
        """Get current provider name"""
        return "ollama" if self.use_ollama else "openai"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information"""
        if self.use_ollama:
            return {
                "provider": "ollama",
                "model": self.ollama_model,
                "url": self.ollama_url
            }
        else:
            return {
                "provider": "openai",
                "model": "gpt-4o",
                "endpoint": self.openai_endpoint
            }
    
    def switch_to_ollama(self, model: str = None, url: str = None):
        """Switch to Ollama provider"""
        self.use_ollama = True
        if model:
            self.ollama_model = model
        if url:
            self.ollama_url = url
    
    def switch_to_openai(self, endpoint: str = None, api_key: str = None):
        """Switch to OpenAI provider"""
        self.use_ollama = False
        if endpoint:
            self.openai_endpoint = endpoint
        if api_key:
            self.openai_key = api_key
    
    def __str__(self):
        info = self.get_model_info()
        return f"API Provider: {info['provider']} | Model: {info['model']}"

# Global configuration instance
api_config = APIConfig()

def get_api_function():
    """Get the appropriate API function based on current configuration"""
    if api_config.use_ollama:
        from src.eval_utils_gpt_aeqa import call_ollama_api
        return lambda sys_prompt, contents: call_ollama_api(
            sys_prompt, contents, 
            model=api_config.ollama_model, 
            ollama_url=api_config.ollama_url
        )
    else:
        from src.eval_utils_gpt_aeqa import call_openai_api
        return call_openai_api

def call_api_configured(sys_prompt, contents) -> Optional[str]:
    """Call the API using current configuration"""
    api_func = get_api_function()
    return api_func(sys_prompt, contents)

# Convenience functions for quick switching
def use_ollama(model: str = None, url: str = None):
    """Switch to Ollama and optionally update model/url"""
    api_config.switch_to_ollama(model, url)
    print(f"Switched to Ollama: {api_config}")

def use_openai(endpoint: str = None, api_key: str = None):
    """Switch to OpenAI and optionally update endpoint/key"""
    api_config.switch_to_openai(endpoint, api_key)
    print(f"Switched to OpenAI: {api_config}")

def get_current_config():
    """Get current configuration info"""
    return api_config.get_model_info()

def print_config():
    """Print current configuration"""
    print(f"Current API Configuration: {api_config}")
    info = api_config.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
