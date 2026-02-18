"""
Ollama handler for managing connections and interactions with the Ollama service.
"""

from typing import List, Dict, Any, Optional
import time

try:
    import tiktoken  # type: ignore[import-untyped]
except ImportError:
    tiktoken = None  # type: ignore[assignment]

try:
    import ollama
    from ollama import Client
except ImportError:
    ollama = None
    Client = None


class OllamaHandler:
    """
    Handles interactions with the Ollama service.
    """

    # TODO: count faulty translations:
    # ========================================
    # Transcription Summary:
    # Total files: 1
    # Successful: 1
    # Failed: 0
    # ========================================

    def __init__(self, host: str = "http://localhost:11434"):
        """
        Initialize the Ollama handler.

        Args:
            host: The URL of the Ollama service.
        """
        if ollama is None:
            raise ImportError(
                "The 'ollama' library is not installed. "
                "Please install it with: pip install ollama"
            )
        
        self.host = host
        self.client = Client(host=host)

    def is_running(self) -> bool:
        """
        Check if the Ollama service is running.

        Returns:
            True if the service is reachable, False otherwise.
        """
        try:
            self.client.list()
            return True
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """
        List available models on the Ollama service.

        Returns:
            List of model names.
        """
        try:
            response = self.client.list()
            # The ollama client may return objects with .models attribute
            # and each model may have .model attribute (not dict with 'name' key)
            models = getattr(response, 'models', None)
            if models is None and isinstance(response, dict):
                models = response.get('models', [])
            if models:
                result = []
                for m in models:
                    name = getattr(m, 'model', None) or getattr(m, 'name', None)
                    if name is None and isinstance(m, dict):
                        name = m.get('model') or m.get('name')
                    if name:
                        result.append(name)
                return result
            return []
        except Exception as e:
            # If service is down, this will raise. We can return empty list or let it raise.
            # For this helper, returning empty list is safer if just checking availability.
            print(f"Warning: Could not list models: {e}")
            return []

    def ensure_model(self, model_name: str) -> bool:
        """
        Check if a model exists.

        Args:
            model_name: The name of the model to check.

        Returns:
            True if the model is available, False otherwise.
        """
        try:
            models = self.list_models()
            # Check for exact match or match before colon (e.g. "translategemma" matches "translategemma:latest")
            # Also handle if user provided "translategemma:latest" but list has "translategemma"
            for m in models:
                if m == model_name:
                    return True
                if m.split(':')[0] == model_name.split(':')[0]:
                    return True
            return False
        except Exception:
            return False

    def generate(self, model: str, prompt: str, **kwargs) -> str:
        """
        Generate text using the specified model.

        Args:
            model: The model name.
            prompt: The input prompt.
            **kwargs: Additional arguments for the generate method.

        Returns:
            The generated text.
        
        Raises:
            ConnectionError: If Ollama is not reachable.
            ValueError: If the model is not found or other error occurs.
        """
        start = time.perf_counter()
        try:
            # We don't explicitly check is_running() here to save a round trip,
            # trusting the client to raise an error if connection fails.
            num_tokens = self.get_token_count(prompt)
            if num_tokens > (4096/2):
                response = self.client.generate(model=model, prompt=prompt, options={"num_ctx": 8096})
            else:
                response = self.client.generate(model=model, prompt=prompt)
            return response['response'] # TODO: sooooo many returns that could be used...use em :(
        except Exception as e:
            str_e = str(e).lower()
            if "connection refused" in str_e or "newconnectionerror" in str_e or "failed to connect" in str_e:
                 raise ConnectionError(
                    f"Ollama service at {self.host} is not reachable. "
                    "Please ensure 'ollama serve' is running."
                ) from e
            if "model" in str_e and "not found" in str_e:
                 raise ValueError(
                    f"Model '{model}' not found. "
                    f"Please pull it using: ollama pull {model}"
                ) from e
            raise e
        finally:
            elapsed = time.perf_counter() - start
            print(f"generate() took {elapsed:.2f} s")

    def get_token_count(self, text: str, encoding_name: str = "cl100k_base") -> int:
        """Return token count for text (for context length checks)."""
        if tiktoken is None:
            raise ImportError(
                "The 'tiktoken' library is not installed. "
                "Please install it with: pip install tiktoken"
            )
        start = time.perf_counter()
        encoding = tiktoken.get_encoding(encoding_name)
        token_count = len(encoding.encode(text))
        elapsed = time.perf_counter() - start
        print(f"get_token_count() took {elapsed:.2f} s")
        return token_count