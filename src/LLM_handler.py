"""
Translate tool for transcribed voice messages.

This module provides translation with Ollama and the translategemma model.
"""

from typing import Optional, List, Dict
import sys
import os
import json

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Try relative import first (for package usage)
    from .ollama_handler import OllamaHandler
except ImportError:
    try:
        from ollama_handler import OllamaHandler
    except ImportError:
        try:
            from src.ollama_handler import OllamaHandler
        except ImportError:
             # Last resort: check if we can add src to path
             sys.path.append(os.path.join(os.getcwd(), 'src'))
             try:
                 from ollama_handler import OllamaHandler
             except ImportError:
                 raise ImportError("Could not import ollama_handler. Please check your python path.")


class LLMHandler:
    """
    Handler for LLM models.
    """

    with open('config.json', 'r') as f:
        config = json.load(f)
    try:
        translate_model_name = config['translate_model']
        summary_model_name = config['summary_model']
    except KeyError:
        raise ValueError("Failed to load models from config.json")

    translate_prompt = """
    Translate the text provided below into english. Maintain the original tone and style.
    
    Input Text: {text}

    Translation:
    """

    summary_prompt = """
    Summarize the text provided below.
    
    Text to summarize: {text}
    
    Summary:
    """

    def __init__(self):
        self.handler = OllamaHandler()
        self.translate_model = self.handler.ensure_model(self.translate_model_name)
        self.summary_model = self.handler.ensure_model(self.summary_model_name)

        # TODO: add error handling
        if not self.translate_model or not self.summary_model:
            raise ValueError("Failed to load models")

    def translate(self, text: str, target_language: str = "en", prompt: Optional[str] = None) -> str:
        if prompt is None:
            prompt = self.translate_prompt
        prompt = prompt.format(text=text, target_language=target_language)
        return self.handler.generate(model=self.translate_model_name, prompt=prompt)['response']

    def summarize(self, text: str, prompt: Optional[str] = None) -> str:
        if prompt is None:
            prompt = self.summary_prompt
        prompt = prompt.format(text=text)
        return self.handler.generate(model=self.summary_model_name, prompt=prompt)['response']
