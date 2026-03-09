"""LLM helper for translation and summarization via local Ollama models."""

import json
from pathlib import Path
from typing import Any, Optional

try:
    from .ollama_handler import OllamaHandler
except ImportError:
    from ollama_handler import OllamaHandler


class LLMHandler:
    """High-level wrapper around configured translation and summary models."""

    translate_prompt = """
    Translate the text provided below into {target_language}. Maintain the original tone and style.

    Input Text: {text}

    Translation:
    """

    summary_prompt = """
    Summarize the text provided below.

    Text to summarize: {text}

    Summary:
    """

    @staticmethod
    def _default_config_path() -> Path:
        return Path(__file__).resolve().parent.parent / "config.json"

    @classmethod
    def _load_config(cls, config_path: Optional[Path] = None) -> dict[str, Any]:
        resolved_path = Path(config_path) if config_path is not None else cls._default_config_path()
        if not resolved_path.exists():
            raise FileNotFoundError(f"Config file not found: {resolved_path}")

        try:
            with resolved_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in config file: {resolved_path}") from exc

    def __init__(self, config_path: Optional[Path] = None):
        config = self._load_config(config_path)
        try:
            self.translate_model_name = config["translate_model"]
            self.summary_model_name = config["summary_model"]
        except KeyError as exc:
            raise ValueError("Missing required model keys in config.json.") from exc

        host = config.get("ollama_host", "http://localhost:11434")
        self.handler = OllamaHandler(host=host)

        self.translate_model = self.handler.ensure_model(self.translate_model_name)
        self.summary_model = self.handler.ensure_model(self.summary_model_name)
        if not self.translate_model or not self.summary_model:
            raise ValueError("Failed to load configured Ollama models.")

    def translate(self, text: str, target_language: str = "en", prompt: Optional[str] = None) -> str:
        if prompt is None:
            prompt = self.translate_prompt
        prompt = prompt.format(text=text, target_language=target_language)
        return self.handler.generate(model=self.translate_model_name, prompt=prompt)["response"]

    def summarize(self, text: str, prompt: Optional[str] = None) -> str:
        if prompt is None:
            prompt = self.summary_prompt
        prompt = prompt.format(text=text)
        return self.handler.generate(model=self.summary_model_name, prompt=prompt)["response"]
