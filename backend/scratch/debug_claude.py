import sys, os, httpx, json, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.core.config import settings

url = "https://api.anthropic.com/v1/messages"
headers = {
    "x-api-key": settings.ANTHROPIC_API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

print("Starting request to claude-haiku-4-5-20251001...", flush=True)
t0 = time.time()
r = httpx.post(
    url,
    headers=headers,
    json={
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1500,
        "system": "Kamu analis makro XAUUSD. Berikan response JSON valid.",
        "messages": [{"role": "user", "content": 'Buat skenario singkat: {"event": "NFP", "price": 4215}'}]
    },
    timeout=30.0
)
print(f"Status: {r.status_code} in {round(time.time() - t0, 2)}s", flush=True)
if r.status_code == 200:
    print("Content preview:", r.json()["content"][0]["text"][:200], flush=True)
else:
    print("Error:", r.text, flush=True)
