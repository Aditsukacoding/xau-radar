from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from app.core.database import Base


class EconomicEvent(Base):
    __tablename__ = "economic_events"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(64), index=True, nullable=True)
    currency = Column(String(8), default="USD", index=True)
    event_title = Column(String(255), nullable=False)
    impact_level = Column(String(16), index=True, default="HIGH")  # HIGH, MEDIUM, LOW
    scheduled_at = Column(DateTime, nullable=False, index=True)
    actual_value = Column(String(32), nullable=True)
    forecast_value = Column(String(32), nullable=True)
    previous_value = Column(String(32), nullable=True)
    unit = Column(String(16), nullable=True)
    sentiment_impact = Column(String(32), nullable=True)  # e.g., BULLISH_USD, BEARISH_USD
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
