import os

from services.ai_generation.llm_connector import LLMConnector


def test_wanai_http_call(monkeypatch):
    # Ensure WAN AI provider is selected via env
    monkeypatch.setenv("WANAI_API_URL", "https://api.wan.example/v1/generate")
    monkeypatch.setenv("WANAI_API_KEY", "fake-key")
    monkeypatch.setenv("LLM_PROVIDER", "wanai")

    # Monkeypatch httpx.Client.post
    class FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"output": ["wanai-response"]}

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, json, headers):
            return FakeResp()

    monkeypatch.setattr("services.ai_generation.llm_connector.httpx.Client", lambda timeout: FakeClient())

    conn = LLMConnector()
    out = conn.generate("hello from wan")
    assert out == "wanai-response"
