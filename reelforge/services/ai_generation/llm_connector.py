"""Environment-driven LLM connector with optional SDK imports.

This module provides `LLMConnector` which selects a provider based on
`LLM_PROVIDER` environment variable or available API keys. SDK imports are
optional and the connector falls back to a lightweight stub when SDKs are
missing.

NOTE: This is a scaffold. Replace TODO sections with full provider
implementations when vendors' SDKs/APIs are integrated.
"""
from __future__ import annotations

import os
from typing import Optional

try:
    import openai as _openai  # type: ignore
except Exception:
    _openai = None

try:
    import google.generativeai as _gemini  # type: ignore
except Exception:
    _gemini = None
    
try:
    import httpx  # type: ignore
except Exception:
    httpx = None


class LLMConnector:
    """Lightweight connector that picks a provider from env or available keys.

    - `LLM_PROVIDER` can be set to `openai` or `gemini` (case-insensitive).
    - If not set the connector will prefer `OPENAI_API_KEY` then `GEMINI/GOOGLE` keys.
    - SDK imports are optional and errors are handled gracefully.
    """

    def __init__(self, provider: Optional[str] = None) -> None:
        self.openai = _openai
        self.gemini = _gemini
        self.provider = (provider or os.getenv("LLM_PROVIDER") or "").lower()

        # Auto-detect when provider not explicitly set
        if not self.provider:
            # Prioritize Wan AI (Alibaba) when configured
            if os.getenv("WANAI_API_KEY") or os.getenv("WAN_AI_API_KEY") or os.getenv("ALIBABA_WANAI_API_KEY"):
                self.provider = "wanai"
            # then OpenAI and Gemini as before
            if os.getenv("OPENAI_API_KEY") and self.openai is not None:
                self.provider = "openai"
            elif (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) and self.gemini is not None:
                self.provider = "gemini"
            elif os.getenv("OPENAI_API_KEY"):
                # SDK missing but key available
                self.provider = "openai"
            elif os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
                self.provider = "gemini"
            else:
                self.provider = "stub"

    def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 256) -> str:
        """Generate text with the selected provider.

        Returns a textual response. On SDK errors a short error string (no secrets)
        or a stub response is returned.
        """
        if self.provider == "openai":
            if not self.openai:
                return self._stub_response(prompt)
            try:
                return self._call_openai(prompt, temperature, max_tokens)
            except Exception as exc:  # do not leak secrets
                return f"openai_error: {str(exc)}"

        if self.provider in ("gemini", "google"):
            if not self.gemini:
                return self._stub_response(prompt)
            try:
                return self._call_gemini(prompt, temperature, max_tokens)
            except Exception as exc:
                return f"gemini_error: {str(exc)}"

        if self.provider in ("wanai", "wan", "alibaba"):
            # Wan AI (Alibaba) via an env-driven HTTP endpoint. Requires
            # WANAI_API_URL and WANAI_API_KEY (or WAN_AI_API_URL/WAN_AI_API_KEY).
            # If not present, fall back to stub.
            if not (os.getenv("WANAI_API_KEY") or os.getenv("WAN_AI_API_KEY") or os.getenv("ALIBABA_WANAI_API_KEY")):
                return self._stub_response(prompt)
            try:
                return self._call_wanai(prompt, temperature, max_tokens)
            except Exception as exc:
                return f"wanai_error: {str(exc)}"

        # fallback stub
        return self._stub_response(prompt)

    def _call_openai(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call OpenAI SDK. This uses a permissive extraction strategy to support
        different versions of the SDK (ChatCompletion vs Completion).

        TODO: Harden to the exact OpenAI SDK you intend to use and add retries.
        """
        if hasattr(self.openai, "ChatCompletion"):
            resp = self.openai.ChatCompletion.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            try:
                return resp["choices"][0]["message"]["content"]
            except Exception:
                # older structures
                if "choices" in resp and resp["choices"]:
                    return resp["choices"][0].get("text", "")
                raise

        if hasattr(self.openai, "Completion"):
            resp = self.openai.Completion.create(
                engine=os.getenv("OPENAI_ENGINE", "text-davinci-003"),
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp["choices"][0].get("text", "")

        raise RuntimeError("openai SDK not available")

    def _call_gemini(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call Google Generative AI (Gemini) SDK. The exact SDK surface varies;
        keep this as a small compatibility shim until the project's API is chosen.

        TODO: Replace with official Gemini SDK usage (models, instantiation, streaming, etc.).
        """
        # Common pattern: google.generativeai.generate_text / text.generate
        if hasattr(self.gemini, "generate_text"):
            resp = self.gemini.generate_text(prompt=prompt, max_output_tokens=max_tokens, temperature=temperature)
            # try a few extraction patterns
            if hasattr(resp, "text"):
                return resp.text
            if isinstance(resp, dict):
                return resp.get("text") or str(resp)
            return str(resp)

        # Last-resort: try a generic callable
        if callable(self.gemini):
            out = self.gemini(prompt)
            return str(out)

        raise RuntimeError("gemini SDK not available")


    def _call_wanai(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call Wan AI (Alibaba) via a generic HTTP API endpoint.

        This implementation is intentionally generic: set `WANAI_API_URL`
        and `WANAI_API_KEY` (or `WAN_AI_API_URL` / `WAN_AI_API_KEY`) in the
        environment. The connector sends a POST with JSON {prompt,...}
        and attempts to extract a textual result from common response shapes.
        """
        if httpx is None:
            raise RuntimeError("httpx is required for WAN AI HTTP calls")

        url = os.getenv("WANAI_API_URL") or os.getenv("WAN_AI_API_URL") or os.getenv("ALIBABA_WANAI_API_URL")
        api_key = os.getenv("WANAI_API_KEY") or os.getenv("WAN_AI_API_KEY") or os.getenv("ALIBABA_WANAI_API_KEY")
        if not url or not api_key:
            raise RuntimeError("WAN AI endpoint or API key not configured")

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"prompt": prompt, "temperature": temperature, "max_tokens": max_tokens}

        # Allow model selection via env
        model = os.getenv("WANAI_MODEL")
        if model:
            payload["model"] = model

        with httpx.Client(timeout=60) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        # Attempt to extract text from common response shapes
        if isinstance(data, dict):
            # common pattern: {'output': ['text', ...]}
            if "output" in data and isinstance(data["output"], list) and data["output"]:
                return data["output"][0]
            if "result" in data:
                r = data["result"]
                if isinstance(r, str):
                    return r
                if isinstance(r, list) and r:
                    return r[0]
            if "text" in data and isinstance(data["text"], str):
                return data["text"]
            # fallback: stringify
            return str(data)

        return str(data)

    def _stub_response(self, prompt: str) -> str:
        """A minimal, local fallback used when no provider is available."""
        return f"[stub] {prompt[:160]}"
