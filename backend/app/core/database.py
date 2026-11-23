import os
import ssl
import logging
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)
DB_INIT_ERROR: str = ""

# Parse & normalize DATABASE_URL cleanly (supports SQLite, Neon, Supabase, standard PostgreSQL)
raw_url = (settings.DATABASE_URL or "").strip()
if raw_url.startswith("psql "):
    raw_url = raw_url[5:].strip()
raw_url = raw_url.strip("'\"")

if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql://", 1)

if not raw_url:
    raw_url = "sqlite:////tmp/trading_analytics.db"

if (os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")) and raw_url.startswith("sqlite"):
    raw_url = "sqlite:////tmp/trading_analytics.db"

def _build_engine(db_url: str):
    global DB_INIT_ERROR
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except OSError:
                db_url = "sqlite:////tmp/trading_analytics.db"
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )

    # PostgreSQL via pure-Python pg8000 (zero C/libpq/glibc issues on Vercel Serverless!)
    try:
        parts = urllib.parse.urlsplit(db_url)
        q_pairs = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
        ssl_requested = True
        clean_q = []
        for k, v in q_pairs:
            kl = k.lower()
            if kl == "sslmode":
                if v.lower() == "disable":
                    ssl_requested = False
                continue
            if kl in ("channel_binding", "options"):
                continue
            clean_q.append((k, v))

        pg_url = urllib.parse.urlunsplit((
            "postgresql+pg8000",
            parts.netloc,
            parts.path,
            urllib.parse.urlencode(clean_q),
            "",
        ))
        c_args = {"timeout": 8}
        if ssl_requested:
            ssl_ctx = ssl.create_default_context()
            c_args["ssl_context"] = ssl_ctx

        # Keep a small warm connection pool (pool_size=2) so queries & commits reuse the TLS socket to Neon!
        return create_engine(
            pg_url,
            connect_args=c_args,
            pool_pre_ping=True,
            pool_recycle=240,
            pool_size=2,
            max_overflow=2,
            echo=False,
        )
    except Exception as e:
        DB_INIT_ERROR = f"{type(e).__name__}: {str(e)[:180]}"
        logger.error(f"[Database] PostgreSQL engine init failed ({DB_INIT_ERROR}), falling back to /tmp SQLite.")
        return create_engine(
            "sqlite:////tmp/trading_analytics.db",
            connect_args={"check_same_thread": False},
            echo=False,
        )

engine = _build_engine(raw_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for obtaining database sessions per request"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
