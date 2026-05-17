"""TikTok helpers: OAuth redirect builder, code exchange, and upload stubs.

This module intentionally keeps provider secrets out of logs and uses
`requests` optionally. The implementations are lightweight scaffolds and
contain TODOs where a production-grade flow (refresh tokens, retries,
chunked upload) is required.
"""

from __future__ import annotations

import os
import urllib.parse
from typing import Dict, Optional

try:
    import requests  # type: ignore
except Exception:
    requests = None


def start_oauth_redirect(state: Optional[str] = None) -> str:
    """Build an OAuth authorization URL for TikTok and return it.

    Environment variables used:
    - `TIKTOK_CLIENT_ID` (required)
    - `TIKTOK_REDIRECT_URI` (required)
    - `TIKTOK_SCOPE` (optional)
    - `TIKTOK_OAUTH_AUTHORIZE_URL` (optional override)
    """
    client_id = os.getenv("TIKTOK_CLIENT_ID")
    redirect_uri = os.getenv("TIKTOK_REDIRECT_URI")
    if not client_id or not redirect_uri:
        raise RuntimeError("TIKTOK_CLIENT_ID and TIKTOK_REDIRECT_URI must be set")

    authorize_url = os.getenv(
        "TIKTOK_OAUTH_AUTHORIZE_URL", "https://open.tiktok.com/platform/oauth/connect"
    )
    params = {
        "client_key": client_id,
        "response_type": "code",
        "scope": os.getenv("TIKTOK_SCOPE", "user.upload"),
        "redirect_uri": redirect_uri,
    }
    if state:
        params["state"] = state

    return authorize_url + "?" + urllib.parse.urlencode(params)


def exchange_code_for_token(code: str, timeout: int = 10) -> Dict[str, Optional[str]]:
    """Exchange an OAuth authorization code for an access token.

    This function performs a simple POST to the token endpoint. It does not
    persist tokens or handle refresh flows. Secrets are read from environment
    and are not logged.

    Returns a dict with token information or raises on HTTP errors.
    """
    token_url = os.getenv("TIKTOK_TOKEN_URL", "https://open.tiktok.com/oauth/access_token/")
    client_key = os.getenv("TIKTOK_CLIENT_ID")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
    redirect_uri = os.getenv("TIKTOK_REDIRECT_URI")

    if not requests:
        # requests not installed; return a stub for tests
        return {"access_token": None, "error": "requests-unavailable"}

    payload = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    # Do not log or return client_secret in responses
    resp = requests.post(token_url, data=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "client_secret" in data:
        data.pop("client_secret", None)
    return data


def upload_tiktok_video(video_url: str, caption: str, hashtags: list | None = None) -> dict:
    """Placeholder TikTok upload adapter.

    Implement OAuth, chunked upload and token refresh in production.
    """
    return {"status": "ok", "platform": "tiktok", "video_url": video_url}


def upload_to_tiktok(video_url: str, caption: str, hashtags: list | None = None) -> dict:
    """Compatibility wrapper used by unit tests and higher-level code."""
    return upload_tiktok_video(video_url, caption, hashtags)
