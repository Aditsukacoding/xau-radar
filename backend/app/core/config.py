from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "Trading Bias Analysis Engine"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    DATABASE_URL: str = "sqlite:///./data/trading_analytics.db"
    USE_MOCK_DATA: bool = False

    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None  # Free fallback: 200+ models via openrouter.ai
    FOREX_NEWS_API_KEY: Optional[str] = None
    TWELVE_DATA_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None

    MANDATORY_DISCLAIMER: str = (
        "PERINGATAN RISIKO & PENAFIAN HUKUM: Seluruh analisis, skor keyakinan, dan ringkasan "
        "dihasilkan otomatis oleh sistem komputasi/AI murni untuk tujuan edukasi dan referensi. "
        "Sistem ini BUKAN saran finansial, ajakan investasi, maupun sinyal eksekusi beli/jual langsung. "
        "Trading instrumen forex dan komoditas memiliki tingkat risiko kerugian yang tinggi."
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
