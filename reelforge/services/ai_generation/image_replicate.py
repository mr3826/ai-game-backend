"""Stub for image generation via external service (Replicate)."""

def generate_image(prompt: str) -> str:
    """Return a placeholder image URL for the prompt.
    TODO: implement actual image generation and return real URL/bytes.
    """
    safe = prompt.replace(" ", "_")
    return f"https://example.com/dummy_image_{safe}.png"

__all__ = ["generate_image"]
