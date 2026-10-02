import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/trading_analytics.db")
os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("IS_WSGI", "true")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("USE_MOCK_DATA", "false")

from app.main import app
