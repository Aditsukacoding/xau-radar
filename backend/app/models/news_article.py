from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime, timezone
from app.core.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(16), index=True, default="XAUUSD")
    title = Column(String(500), nullable=False)
    source = Column(String(100), default="Market News")
    url = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    sentiment_label = Column(String(16), default="NEUTRAL")  # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score = Column(Float, default=0.0)  # -1.0 to +1.0
    published_at = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
