import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure environment for Vercel serverless
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/trading_analytics.db")
os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("IS_WSGI", "true")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("USE_MOCK_DATA", "false")

from api.index import app
