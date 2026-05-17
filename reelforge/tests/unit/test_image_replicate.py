def test_import_generate_image():
    from services.ai_generation.image_replicate import generate_image
    assert callable(generate_image)
    url = generate_image("a test prompt")
    assert isinstance(url, str)
