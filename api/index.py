import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/trading_analytics.db")
os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("IS_WSGI", "true")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("USE_MOCK_DATA", "false")

from app.main import app as _app

async def app(scope, receive, send):
    """
    ASGI middleware for Vercel serverless.
    Restores the original requested path from Vercel's x-matched-path header
    so FastAPI routes (/health, /api/v1/..., etc.) match accurately.
    """
    if scope.get("type") == "http":
        headers = dict(scope.get("headers", []))
        matched_path = headers.get(b"x-matched-path", b"").decode("utf-8", "ignore")
        if matched_path:
            scope["path"] = matched_path.split("?")[0]
        elif scope.get("path") in ("/api/index.py", "/api/index", "/api", ""):
            scope["path"] = "/"

    await _app(scope, receive, send)
