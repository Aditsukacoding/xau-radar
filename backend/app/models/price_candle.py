from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from datetime import datetime, timezone
from app.core.database import Base


class PriceCandle(Base):
    __tablename__ = "price_candles"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(16), index=True, nullable=False)
    timeframe = Column(String(8), index=True, nullable=False)  # 5m, 15m, 1h, 4h, 1d
    timestamp = Column(DateTime, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp", name="uq_candle_symbol_tf_time"),
    )
