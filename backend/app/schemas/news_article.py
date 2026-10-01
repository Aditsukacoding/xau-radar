from pydantic import BaseModel, ConfigDict
from datetime import datetime
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

    model_config = ConfigDict(from_attributes=True)
