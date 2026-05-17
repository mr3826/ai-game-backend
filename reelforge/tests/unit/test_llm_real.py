import os

from services.ai_generation.llm_connector import LLMConnector


def test_generate_openai(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    conn = LLMConnector()
    # Monkeypatch the instance-level provider call to avoid real network calls
    monkeypatch.setattr(conn, "_call_openai", lambda prompt, temperature, max_tokens: "openai-response")
    assert conn.generate("hello world") == "openai-response"


def test_generate_gemini(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    conn = LLMConnector()
    monkeypatch.setattr(conn, "_call_gemini", lambda prompt, temperature, max_tokens: "gemini-response")
    assert conn.generate("hi") == "gemini-response"
