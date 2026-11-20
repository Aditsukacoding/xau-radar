from pydantic import BaseModel, ConfigDict, field_serializer
from datetime import datetime, timezone
from typing import Optional


class NewsArticleBase(BaseModel):
    symbol: str = "XAUUSD"
    title: str
    source: str = "Market News"
    url: Optional[str] = None
    summary: Optional[str] = None
    sentiment_label: str = "NEUTRAL"
    sentiment_score: float = 0.0
    published_at: datetime


class NewsArticleCreate(NewsArticleBase):
    pass


class NewsArticleResponse(NewsArticleBase):
    id: int
    created_at: datetime

    @field_serializer("published_at", "created_at")
    def serialize_utc_dt(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    model_config = ConfigDict(from_attributes=True)
