"""Minimal LLM connector wrapper (Gemini primary, OpenAI fallback)."""
import os

class LLMConnector:
    """
    Minimal config-backed wrapper for LLM calls.
    TODO: replace stub logic with real API calls.
    """
    def __init__(self, provider: str | None = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "gemini")

    def generate(self, prompt: str) -> str:
        """Return a placeholder response for the given prompt."""
        if self.provider.lower() == "gemini":
            # TODO: implement Gemini client
            return f"Gemini (stub) response for: {prompt}"
        # fallback to OpenAI
        return f"OpenAI (stub) response for: {prompt}"

__all__ = ["LLMConnector"]
