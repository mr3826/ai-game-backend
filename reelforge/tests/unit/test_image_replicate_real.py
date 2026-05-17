import os

import httpx


def test_generate_image_monkeypatched(monkeypatch):
    from services.ai_generation.image_replicate import generate_image

    # Install a fake token so the function attempts an HTTP call
    monkeypatch.setenv("REPLICATE_API_TOKEN", "fake-token")

    class FakeResp:
        status_code = 201

        def raise_for_status(self):
            return None

        def json(self):
            return {"output": ["https://example.com/fake.png"]}

    def fake_post(url, json, headers):
        return FakeResp()

    monkeypatch.setattr(httpx, "post", fake_post)

    url = generate_image("a test prompt")
    assert isinstance(url, str)
    assert url.startswith("https://")
