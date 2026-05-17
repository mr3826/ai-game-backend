"""Replicate image generation adapter with REST fallback.

Uses `REPLICATE_API_TOKEN` to call Replicate's REST API when available.
If `requests` isn't installed or `REPLICATE_API_TOKEN` is not set, falls back
to a local stub implementation.

TODO: Replace placeholder model/version with a concrete model and add
long-running prediction polling and error handling as appropriate.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

try:
    import requests  # type: ignore
except Exception:
    requests = None


REPLICATE_URL = "https://api.replicate.com/v1/predictions"


def generate_image(prompt: str, model_version: Optional[str] = None, timeout: int = 30) -> Any:
    """Generate an image using Replicate's REST API.

    Returns the parsed JSON response on success, or a stub string if the
    token/SDK is not available.
    """
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token or not requests:
        return _stub_generate(prompt)

    payload: Dict[str, Any] = {
        "input": {"prompt": prompt},
    }
    # The exact Replicate API expects a `version` string for the model. Allow
    # overriding via env or argument.
    version = model_version or os.getenv("REPLICATE_MODEL_VERSION") or "placeholder/model:version"
    payload["version"] = version

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    resp = requests.post(REPLICATE_URL, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    # Replicate typically returns an `output` array for predictions. Return
    # the first element when present, otherwise the full response.
    out = data.get("output")
    if isinstance(out, list) and out:
        return out[0]
    return data


def _stub_generate(prompt: str) -> str:
    return f"[replicate-stub] {prompt[:120]}"
