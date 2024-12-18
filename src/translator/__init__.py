from typing import Optional
import yaml
from .base import BaseTranslator
from .openai_translator import OpenAITranslator

def create_translator(config_path: str = "config.yaml") -> BaseTranslator:
    """
    Factory function to create appropriate translator instance
    
    Args:
        config_path (str): Path to configuration file
        
    Returns:
        BaseTranslator: Configured translator instance
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        raise Exception(f"Failed to load config file: {e}")

    # Currently only OpenAI is supported
    # Future implementations can be added here based on config
    return OpenAITranslator(config_path)

__all__ = ['BaseTranslator', 'OpenAITranslator', 'create_translator']
