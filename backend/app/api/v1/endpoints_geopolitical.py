from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.news_article import NewsArticle
from app.schemas.news_article import NewsArticleResponse
from app.services.ingestion_service import IngestionService

router = APIRouter()


@router.get("/news", response_model=List[NewsArticleResponse])
async def get_geopolitical_news(
    symbol: str = Query("XAUUSD", description="Instrument symbol"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment: POSITIVE, NEGATIVE, NEUTRAL"),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get live geopolitical and macroeconomic news articles with sentiment scoring.
    Automatically checks and ingests fresh breaking news if database is stale (> 2 minutes).
    """
    # Auto-refresh breaking news if newest article is older than 2 minutes
    try:
        await IngestionService.auto_refresh_if_stale(db, symbol=symbol, max_age_seconds=120)
    except Exception:
        pass

    query = db.query(NewsArticle).filter(NewsArticle.symbol == symbol.upper())

    if sentiment:
        query = query.filter(NewsArticle.sentiment_label == sentiment.upper())

    return query.order_by(desc(NewsArticle.published_at)).limit(limit).all()


@router.post("/news/sync", response_model=List[NewsArticleResponse])
async def trigger_news_sync(
    symbol: str = Query("XAUUSD", description="Instrument symbol"),
    db: Session = Depends(get_db),
):
    """
    Explicitly trigger an instant breaking news ingestion from all global feeds.
    """
    await IngestionService.ingest_latest_news(db, symbol=symbol)
    return db.query(NewsArticle).filter(NewsArticle.symbol == symbol.upper()).order_by(desc(NewsArticle.published_at)).limit(30).all()
