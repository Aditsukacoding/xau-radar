import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from app.core.database import get_db
from app.models.instrument import Instrument
from app.models.analysis_report import AnalysisReport
from app.models.economic_event import EconomicEvent
from app.models.news_article import NewsArticle
from app.models.price_candle import PriceCandle
from app.schemas.instrument import InstrumentResponse
from app.schemas.analysis_report import DashboardSummaryResponse, TradeSetup
from app.providers import get_data_provider
from app.services.technical_calc import TechnicalCalculator
from app.services.analysis_service import AnalysisService
from app.services.ingestion_service import IngestionService

router = APIRouter()


@router.get("/instruments", response_model=List[InstrumentResponse])
def get_instruments(db: Session = Depends(get_db)):
    """List all supported instruments (e.g. XAUUSD)"""
    return db.query(Instrument).filter(Instrument.is_active == True).all()


@router.get("/summary/{symbol}", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(symbol: str = "XAUUSD", db: Session = Depends(get_db)):
    """
    Get consolidated dashboard metrics:
    - Real-time price snapshot
    - Overall AI Bias & Confidence Score
    - Upcoming High Impact Event radar
    - Latest Geopolitical News headline
    - Technical indicator summary
    - Mandatory legal disclaimer
    """
    symbol = symbol.upper()
    instrument = db.query(Instrument).filter(Instrument.symbol == symbol).first()
    if not instrument:
        raise HTTPException(status_code=404, detail=f"Instrument '{symbol}' not found")

    provider = get_data_provider()
    price_info = await provider.get_latest_price(symbol)

    # Latest Analysis Report
    report = await AnalysisService.get_or_generate_analysis(db, symbol=symbol)

    # Next High Impact Event
    now = datetime.now(timezone.utc)
    next_event = (
        db.query(EconomicEvent)
        .filter(EconomicEvent.impact_level == "HIGH", EconomicEvent.scheduled_at >= now)
        .order_by(EconomicEvent.scheduled_at.asc())
        .first()
    )
    event_dict = None
    if next_event:
        event_dict = {
            "title": next_event.event_title,
            "impact": next_event.impact_level,
            "scheduled_at": next_event.scheduled_at.isoformat(),
            "currency": next_event.currency,
            "forecast": next_event.forecast_value,
            "previous": next_event.previous_value,
        }

    # Latest News
    latest_news = (
        db.query(NewsArticle)
        .filter(NewsArticle.symbol == symbol)
        .order_by(desc(NewsArticle.published_at))
        .first()
    )
    news_dict = None
    if latest_news:
        news_dict = {
            "title": latest_news.title,
            "source": latest_news.source,
            "sentiment_label": latest_news.sentiment_label,
            "sentiment_score": latest_news.sentiment_score,
            "published_at": latest_news.published_at.isoformat(),
        }

    # Technical quick check
    candles = (
        db.query(PriceCandle)
        .filter(PriceCandle.symbol == symbol, PriceCandle.timeframe == "1h")
        .order_by(PriceCandle.timestamp.asc())
        .all()
    )
    candles_list = [
        {"open": c.open, "high": c.high, "low": c.low, "close": c.close, "volume": c.volume, "timestamp": c.timestamp}
        for c in candles
    ]
    tech_data = TechnicalCalculator.calculate_indicators(candles_list)

    trade_setup_raw = json.loads(report.trade_setup_json) if getattr(report, 'trade_setup_json', None) else None
    trade_setup_obj = TradeSetup(**trade_setup_raw) if trade_setup_raw else None

    return DashboardSummaryResponse(
        symbol=symbol,
        instrument_name=instrument.name,
        current_price=price_info["current_price"],
        price_change_24h=price_info["change_24h"],
        price_change_pct_24h=price_info["change_pct_24h"],
        high_24h=price_info["high"],
        low_24h=price_info["low"],
        bias=report.bias,
        confidence_score=report.confidence_score,
        bias_summary=report.summary,
        trade_setup=trade_setup_obj,
        upcoming_high_impact_event=event_dict,
        latest_geopolitical_headline=news_dict,
        technical_snapshot={
            "trend": tech_data.get("trend_direction", "NEUTRAL"),
            "rsi": tech_data.get("rsi_14"),
            "rsi_status": tech_data.get("rsi_condition"),
            "summary": tech_data.get("summary"),
        },
        disclaimer=report.disclaimer,
        last_updated=report.created_at,
    )


@router.post("/sync/{symbol}", response_model=DashboardSummaryResponse)
async def trigger_full_live_sync(symbol: str = "XAUUSD", db: Session = Depends(get_db)):
    """
    Trigger full live real-time sync:
    - Fetches fresh Gold prices and candles from Yahoo Finance
    - Fetches fresh economic calendar events from ForexFactory
    - Ingests fresh global financial news
    - Synthesizes fresh AI market bias report
    """
    await IngestionService.sync_live_market_data(db, symbol=symbol.upper())
    return await get_dashboard_summary(symbol=symbol, db=db)
