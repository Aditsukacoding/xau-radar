from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone
from app.core.database import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(16), unique=True, index=True, nullable=False)
    name = Column(String(64), nullable=False)
    category = Column(String(32), default="commodity")  # commodity, forex, crypto
    base_currency = Column(String(8), default="XAU")
    quote_currency = Column(String(8), default="USD")
    pip_decimal = Column(Integer, default=2)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
