import os

from types import SimpleNamespace

import pytest

from services.ai_generation import image_replicate


def test_generate_image_with_replicate_token(monkeypatch):
    monkeypatch.setenv("REPLICATE_API_TOKEN", "fake-token")

    class FakeResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"output": ["https://example.com/image.png"]}

    def fake_post(url, json, headers, timeout):
        assert "Authorization" in headers and headers["Authorization"].startswith("Token")
        return FakeResp()

    monkeypatch.setattr(image_replicate, "requests", SimpleNamespace(post=fake_post))

    out = image_replicate.generate_image("a red apple on a table")
    assert out == "https://example.com/image.png"


def test_generate_image_stub(monkeypatch):
    # Ensure no token -> stub path
    monkeypatch.delenv("REPLICATE_API_TOKEN", raising=False)
    monkeypatch.setattr(image_replicate, "requests", None)
    out = image_replicate.generate_image("sunset over mountains")
    assert out.startswith("[replicate-stub]")
