import sys
import os
import urllib.parse

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
    ASGI middleware for Vercel Serverless Function.
    Restores the exact original requested URL path passed via rewrite query parameter.
    """
    if scope.get("type") == "http":
        qs = scope.get("query_string", b"").decode("utf-8", "ignore")
        if "__path=" in qs:
            params = urllib.parse.parse_qs(qs, keep_blank_values=True)
            if "__path" in params:
                raw_path = params.pop("__path")[0]
                if not raw_path.startswith("/"):
                    raw_path = "/" + raw_path
                scope["path"] = raw_path
                scope["raw_path"] = raw_path.encode("utf-8")
                new_qs = urllib.parse.urlencode(params, doseq=True)
                scope["query_string"] = new_qs.encode("utf-8")
        elif scope.get("path") in ("/api/index.py", "/api/index", "/api"):
            scope["path"] = "/"
            scope["raw_path"] = b"/"

    await _app(scope, receive, send)
