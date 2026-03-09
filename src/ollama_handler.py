"""
Ollama handler for managing connections and interactions with the Ollama service.
"""

from typing import List, Dict, Any, Optional
import time

from app_logging import get_logger

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

logger = get_logger(__name__)


class OllamaHandler:
    """
    Handles interactions with the Ollama service.
    """

    def __init__(self, host: str = "http://localhost:11434"):  # TODO: Read default host from centralized settings.
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
            # service is down
            logger.warning("Could not list models: %s", e)
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
            for m in models:
                if m == model_name:
                    return True
                # FIXME(uncertain): Base-name matching may produce false positives for missing tags.
                if m.split(':')[0] == model_name.split(':')[0]:
                    return True
            return False
        except Exception as e:
            logger.warning("Could not ensure model: %s", e)
            return False

    def generate(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text using the specified model.

        Args:
            model: The model name.
            prompt: The input prompt.
            **kwargs: Additional arguments for the generate method.

        Returns:
            A dictionary with:
                - 'response': The generated text,
                - 'elapsed': Time in seconds for generation,
                - 'tokens': Input prompt token count
        Raises:
            ConnectionError: If Ollama is not reachable.
            ValueError: If the model is not found or other error occurs.
        """
        start = time.perf_counter()
        num_tokens: Optional[int] = None
        try:
            num_tokens = self.get_token_count(prompt)
        except Exception:
            # Token counting is optional and should never block generation.
            num_tokens = None

        try:
            # TODO: Revisit context sizing strategy for long prompts.
            generate_kwargs = dict(kwargs)
            if num_tokens is not None and num_tokens > (4096 / 2):
                options = generate_kwargs.get("options")
                if isinstance(options, dict):
                    options = dict(options)
                    options.setdefault("num_ctx", 8096)
                    generate_kwargs["options"] = options
                elif options is None:
                    generate_kwargs["options"] = {"num_ctx": 8096}

            response = self.client.generate(model=model, prompt=prompt, **generate_kwargs)
            output_text = response['response']
            return {
                'response': output_text,
                'elapsed': time.perf_counter() - start,
                'tokens': num_tokens
            }
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
            raise

    def get_token_count(self, text: str, encoding_name: str = "cl100k_base") -> int:
        """Return token count for text (for context length checks)."""
        if tiktoken is None:
            raise ImportError(
                "The 'tiktoken' library is not installed. "
                "Please install it with: pip install tiktoken"
            )
        encoding = tiktoken.get_encoding(encoding_name)
        token_count = len(encoding.encode(text))
        return token_count