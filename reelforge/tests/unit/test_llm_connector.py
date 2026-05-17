def test_import_llm_connector():
    from services.ai_generation.llm_connector import LLMConnector
    c = LLMConnector()
    assert callable(c.generate)
    assert isinstance(c.generate("hello"), str)
