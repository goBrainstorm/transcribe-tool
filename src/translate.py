"""
Translate tool for transcribed voice messages.

This module provides translation with Ollama and the translategemma model.
"""

from typing import Optional, List, Dict
import sys
import os

# Ensure we can import from the same directory if run directly
# This allows running 'python src/translate.py' from project root or src/
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Try relative import first (for package usage)
    from .ollama_handler import OllamaHandler
except ImportError:
    try:
        # Try direct import (for script usage within src)
        from ollama_handler import OllamaHandler
    except ImportError:
        # Try import from src (for script usage from root)
        try:
            from src.ollama_handler import OllamaHandler
        except ImportError:
             # Last resort: check if we can add src to path
             sys.path.append(os.path.join(os.getcwd(), 'src'))
             try:
                 from ollama_handler import OllamaHandler
             except ImportError:
                 raise ImportError("Could not import ollama_handler. Please check your python path.")


class TranslateTool:
    """
    Translate tool for transcribed voice messages using Ollama.

    Usage:
        # Initialize with default settings
        tool = TranslateTool()
        
        # Check if service is available
        health = tool.check_health()
        if health["ollama_running"]:
            # Translate text
            result = tool.translate("Hello world", "de")
            print(result)
    """

    def __init__(
        self,
        ollama_handler: Optional[OllamaHandler] = None,
        translate_model_name: str = "translategemma:4b"
    ):
        """
        Initialize the TranslateTool.

        Args:
            ollama_handler: An instance of OllamaHandler. If None, a new one is created.
            model_name: The name of the translation model to use (default: "translategemma:4b").
        """
        self.model_name = translate_model_name
        self.handler = ollama_handler or OllamaHandler()
        
        # Check if service is running
        if not self.handler.is_running():
            print(
                f"Warning: Ollama service does not appear to be running at {self.handler.host}. "
                "Translation functionality will not work until 'ollama serve' is started."
            )
        else:
            # Check if model is available
            # We use ensure_model which checks availability but doesn't pull automatically
            # to avoid blocking without feedback
            if not self.handler.ensure_model(self.model_name):
                 print(
                    f"Warning: Model '{self.model_name}' not found. "
                    f"Please pull it using: ollama pull {self.model_name}"
                )

    def translate(self, text: str, target_language: str = "en", source_language: str = "auto") -> str:
        """
        Translate the given text to the target language.

        Args:
            text: The text to translate.
            target_language: The target language code (e.g., "en", "de", "fr").
            source_language: The source language code (default: "auto").

        Returns:
            The translated text.
        
        Raises:
            ConnectionError: If Ollama service is not reachable.
            ValueError: If the model is not found or other error occurs.
        """
        if not text:
            return ""

        # Construct the prompt for translategemma
        # Format: Translate from [source] to [target]: [text]
        # If source is auto, we try to infer or use a generic prompt.
        
        if source_language == "auto":
             # For translategemma, explicit source is better, but let's try a direct request
             prompt = f"Translate to {target_language}: {text}"
        else:
             prompt = f"Translate from {source_language} to {target_language}: {text}"

        try:
            return self.handler.generate(model=self.model_name, prompt=prompt)
        except Exception as e:
            # Re-raise with context if needed, but handler already raises specific errors
            raise e

    def check_health(self) -> Dict[str, bool]:
        """
        Check the health of the translation service.

        Returns:
            A dictionary with status information.
        """
        is_running = self.handler.is_running()
        model_available = False
        if is_running:
            model_available = self.handler.ensure_model(self.model_name)
        
        return {
            "ollama_running": is_running,
            "model_available": model_available
        }

    def list_available_models(self) -> List[str]:
        """
        List all available models in Ollama.

        Returns:
            List of model names.
        """
        return self.handler.list_models()


if __name__ == "__main__":
    # Example usage
    try:
        print("Initializing TranslateTool...")
        tool = TranslateTool()
        
        health = tool.check_health()
        print(f"Health check: {health}")
        
        if health["ollama_running"] and health["model_available"]:
            text = "Hello, how are you today?"
            target = "de"
            print(f"Translating '{text}' to {target}...")
            result = tool.translate(text, target)
            print(f"Result: {result}")
        else:
            print("Skipping translation check because service or model is unavailable.")
            if not health["ollama_running"]:
                print("Run 'ollama serve' to start the service.")
            if not health["model_available"]:
                print(f"Run 'ollama pull {tool.model_name}' to download the model.")
                
    except ImportError as e:
        print(f"ImportError: {e}")
        print("Please ensure requirements are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"Error: {e}")
