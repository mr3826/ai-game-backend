"""Replicate image connector (HTTP-based) with local fallback.

Uses `REPLICATE_API_TOKEN` and optional `REPLICATE_MODEL_VERSION` environment variables.
Falls back to a local placeholder URL when the token is missing or the request fails.
"""
from __future__ import annotations

import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def _extract_output(resp_json: dict) -> Optional[str]:
    # Common patterns: {"output": [url, ...]} or {"result": url} or nested structures
    if not isinstance(resp_json, dict):
        return None
    if "output" in resp_json and isinstance(resp_json["output"], list) and resp_json["output"]:
        return resp_json["output"][0]
    if "result" in resp_json:
        r = resp_json["result"]
        if isinstance(r, list) and r:
            return r[0]
        if isinstance(r, str):
            return r
    # Try nested keys
    for key in ("prediction", "predictions", "data"):
        if key in resp_json:
            val = resp_json[key]
            if isinstance(val, list) and val:
                first = val[0]
                if isinstance(first, str):
                    return first
                if isinstance(first, dict) and "url" in first:
                    return first["url"]
    return None


def generate_image(prompt: str, model_version: Optional[str] = None, timeout: int = 60) -> str:
    """Generate an image using Replicate's REST API.

    Returns a URL-like string pointing to the generated image, or a local placeholder URL on failure.
    """
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        # No token: fallback to a placeholder image URL
        safe = prompt.replace(" ", "_")[:100]
        return f"https://example.com/dummy_image_{safe}.png"

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    api_url = "https://api.replicate.com/v1/predictions"
    model_ver = model_version or os.getenv("REPLICATE_MODEL_VERSION")

    payload = {"input": {"prompt": prompt}}
    if model_ver:
        payload["version"] = model_ver

    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(api_url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            out = _extract_output(data)
            if out:
                return out
            # Some APIs return URLs under `urls` or nested places
            return str(data)
    except Exception:
        logger.exception("Replicate image generation failed, falling back to placeholder")
        safe = prompt.replace(" ", "_")[:100]
        return f"https://example.com/dummy_image_{safe}.png"


__all__ = ["generate_image"]
