import os
import hashlib
import json
from redis import Redis

try:
    redis = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
except Exception:
    redis = None


def generate_script(brand: str, niche: str, trend: str, style: str | None = None) -> dict:
    """Lightweight placeholder LLM: returns a simple script and caches it in Redis.

    Replace with Gemini/OpenAI API calls in production.
    """
    prompt = f"Brand: {brand}\nNiche: {niche}\nTrend: {trend}\nProduce: hook, body, cta, scenes."
    key = "script:" + hashlib.sha256(prompt.encode()).hexdigest()
    try:
        cached = redis.get(key) if redis else None
    except Exception:
        cached = None
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    result = {
        "hook": f"Quick take: {trend}",
        "body": f"Short explanation for {niche} audience: {trend} - condensed.",
        "cta": "Follow for more AI tips.",
        "scenes": [f"Scene prompt about {trend} #{i}" for i in range(1, 4)],
    }
    try:
        if redis:
            redis.setex(key, 86400, json.dumps(result))
    except Exception:
        pass
    return result
