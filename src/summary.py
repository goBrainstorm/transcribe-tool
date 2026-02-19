import sys
import os
import time
from typing import Optional

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

class Summary_Tool:
    """Summary of the translations."""

    def __init__(
        self, 
        ollama_handler: Optional[OllamaHandler] = None, 
        summary_model_name: str = "qwen3:0.6b" # TODO: add model selection
    ):
        """Initialize the Summary instance."""
        self.model_name = summary_model_name
        self.handler = ollama_handler or OllamaHandler()
        
        # Check if service is running
        if not self.handler.is_running():
            print(
                f"Warning: Ollama service does not appear to be running at {self.handler.host}. "
                "Summary functionality will not work until 'ollama serve' is started."
            )
        else:
            # Check if model is available
            if not self.handler.ensure_model(self.model_name):
                 print(
                    f"Warning: Model '{self.model_name}' not found. "
                    f"Please pull it using: ollama pull {self.model_name}"
                )

    def check_health(self) -> Dict[str, bool]:
        """
        Check the health of the summary service.

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

    def summarize(self, text: str, language: str = "en") -> str:
        """Summarize the text."""
        if not text:
            return None
        start = time.perf_counter()
        
        prompt = f"""Instruction: Summarize the following text. Maintain the original tone and style.
        
        Input Text: {text}
                
        Summary:
        """
        try:
            return self.handler.generate(model=self.model_name, prompt=prompt)
        except Exception as e:
            raise e
        finally:
            elapsed = time.perf_counter() - start
            print(f"summarize() took {elapsed:.2f} s")
