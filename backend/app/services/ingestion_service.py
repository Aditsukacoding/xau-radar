import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.instrument import Instrument
from app.models.economic_event import EconomicEvent
from app.models.news_article import NewsArticle
from app.models.price_candle import PriceCandle
from app.models.analysis_report import AnalysisReport
from app.providers import get_data_provider
from app.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)


class IngestionService:
    @staticmethod
    async def seed_initial_data_if_empty(db: Session):
        """
        Seeds default instrument (XAUUSD), initial candles, economic events,
        and news if database is newly initialized.
        """
        provider = get_data_provider()

        # 1. Seed Instrument
        xau = db.query(Instrument).filter(Instrument.symbol == "XAUUSD").first()
        if not xau:
            logger.info("Seeding default instrument XAUUSD...")
            xau = Instrument(
                symbol="XAUUSD",
                name="Gold vs US Dollar",
                category="commodity",
                base_currency="XAU",
                quote_currency="USD",
                pip_decimal=2,
                is_active=True,
            )
            db.add(xau)
            db.commit()

        # 2. Seed Economic Events
        event_count = db.query(EconomicEvent).count()
        if event_count == 0:
            logger.info("Fetching real/initial economic calendar events...")
            raw_events = await provider.get_economic_calendar()
            for ev in raw_events:
                event_obj = EconomicEvent(
                    external_id=ev.get("external_id"),
                    currency=ev.get("currency", "USD"),
                    event_title=ev.get("event_title"),
                    impact_level=ev.get("impact_level", "HIGH"),
                    scheduled_at=ev.get("scheduled_at"),
                    actual_value=ev.get("actual_value"),
                    forecast_value=ev.get("forecast_value"),
                    previous_value=ev.get("previous_value"),
                    unit=ev.get("unit"),
                    sentiment_impact=ev.get("sentiment_impact"),
                )
                db.add(event_obj)
            db.commit()

        # 3. Seed News Articles
        news_count = db.query(NewsArticle).count()
        if news_count == 0:
            logger.info("Fetching real/initial geopolitical & market news...")
            raw_news = await provider.get_news_articles(symbol="XAUUSD", limit=20)
            for nw in raw_news:
                news_obj = NewsArticle(
                    symbol=nw.get("symbol", "XAUUSD"),
                    title=nw.get("title"),
                    source=nw.get("source"),
                    url=nw.get("url"),
                    summary=nw.get("summary"),
                    sentiment_label=nw.get("sentiment_label", "NEUTRAL"),
                    sentiment_score=nw.get("sentiment_score", 0.0),
                    published_at=nw.get("published_at"),
                )
                db.add(news_obj)
            db.commit()

        # 4. Seed Candles for 15m, 1h, 1d
        candle_count = db.query(PriceCandle).filter(PriceCandle.symbol == "XAUUSD").count()
        if candle_count == 0:
            logger.info("Fetching real/initial candlestick price data...")
            for tf in ["15m", "1h", "1d"]:
                raw_candles = await provider.get_price_candles(symbol="XAUUSD", timeframe=tf, count=80)
                for c in raw_candles:
                    candle_obj = PriceCandle(
                        symbol=c["symbol"],
                        timeframe=c["timeframe"],
                        timestamp=c["timestamp"],
                        open=c["open"],
                        high=c["high"],
                        low=c["low"],
                        close=c["close"],
                        volume=c["volume"],
                    )
                    db.add(candle_obj)
            db.commit()

        # 5. Generate initial Analysis Report instantly (< 50ms)
        report_count = db.query(AnalysisReport).filter(AnalysisReport.symbol == "XAUUSD").count()
        if report_count == 0:
            logger.info("Generating instant quantitative baseline report (<50ms)...")
            await AnalysisService._generate_instant_baseline(db, symbol="XAUUSD")

    @staticmethod
    async def sync_live_market_data(db: Session, symbol: str = "XAUUSD"):
        """
        Actively syncs real-time live data:
        1. Refreshes real candlestick data from Yahoo Finance
        2. Ingests fresh live economic calendar events
        3. Ingests latest live news articles
        4. Re-synthesizes AI market bias report
        """
        provider = get_data_provider()
        # 0. Syncing live candles
        logger.info(f"Syncing real live market data for {symbol}...")

        # 1. Update Candles for ALL supported timeframes
        for tf in ["5m", "15m", "1h", "4h", "1d"]:
            raw_candles = await provider.get_price_candles(symbol=symbol, timeframe=tf, count=80)
            for c in raw_candles:
                existing = (
                    db.query(PriceCandle)
                    .filter(
                        PriceCandle.symbol == symbol,
                        PriceCandle.timeframe == tf,
                        PriceCandle.timestamp == c["timestamp"],
                    )
                    .first()
                )
                if not existing:
                    db.add(PriceCandle(
                        symbol=symbol,
                        timeframe=tf,
                        timestamp=c["timestamp"],
                        open=c["open"],
                        high=c["high"],
                        low=c["low"],
                        close=c["close"],
                        volume=c["volume"],
                    ))
                else:
                    existing.close = c["close"]
                    existing.high = max(existing.high, c["high"])
                    existing.low = min(existing.low, c["low"])
        db.commit()

        # 2. Ingest News
        raw_news = await provider.get_news_articles(symbol=symbol, limit=15)
        for nw in raw_news:
            exists = db.query(NewsArticle).filter(NewsArticle.title == nw["title"]).first()
            if not exists:
                db.add(NewsArticle(
                    symbol=symbol,
                    title=nw["title"],
                    source=nw["source"],
                    url=nw.get("url"),
                    summary=nw.get("summary"),
                    sentiment_label=nw["sentiment_label"],
                    sentiment_score=nw["sentiment_score"],
                    published_at=nw["published_at"],
                ))
        db.commit()

        # 3. Ingest Calendar
        raw_events = await provider.get_economic_calendar()
        for ev in raw_events:
            ext_id = ev.get("external_id")
            if ext_id:
                exists = db.query(EconomicEvent).filter(EconomicEvent.external_id == ext_id).first()
                if not exists:
                    db.add(EconomicEvent(
                        external_id=ext_id,
                        currency=ev["currency"],
                        event_title=ev["event_title"],
                        impact_level=ev["impact_level"],
                        scheduled_at=ev["scheduled_at"],
                        actual_value=ev.get("actual_value"),
                        forecast_value=ev.get("forecast_value"),
                        previous_value=ev.get("previous_value"),
                        sentiment_impact=ev.get("sentiment_impact"),
                    ))
        db.commit()

        # 4. Generate Fresh Analysis with real-time data
        return await AnalysisService.generate_fresh_analysis(db, symbol=symbol)

    @staticmethod
    async def ingest_latest_news(db: Session, symbol: str = "XAUUSD") -> int:
        """
        Fetches breaking real-time news from multi-stream feeds and ingests any new articles.
        Returns count of newly ingested articles.
        """
        provider = get_data_provider()
        raw_news = await provider.get_news_articles(symbol=symbol, limit=30)
        new_count = 0
        for nw in raw_news:
            exists = db.query(NewsArticle).filter(
                (NewsArticle.title == nw["title"]) | (NewsArticle.url == nw.get("url"))
            ).first()
            if not exists:
                db.add(NewsArticle(
                    symbol=symbol.upper(),
                    title=nw["title"],
                    source=nw["source"],
                    url=nw.get("url"),
                    summary=nw.get("summary"),
                    sentiment_label=nw["sentiment_label"],
                    sentiment_score=nw["sentiment_score"],
                    published_at=nw["published_at"],
                ))
                new_count += 1
        if new_count > 0:
            db.commit()
            logger.info(f"Ingested {new_count} new breaking news articles into database.")
        return new_count

    @staticmethod
    async def ingest_latest_calendar(db: Session) -> int:
        """
        Fetches latest economic calendar events from ForexFactory and performs a full upsert:
        - Inserts new events never seen before
        - Updates forecast, previous, and actual values when data changes (actuals released intraday)
        Returns count of inserted or updated records.
        """
        provider = get_data_provider()
        raw_events = await provider.get_economic_calendar()
        updated_count = 0
        for ev in raw_events:
            ext_id = ev.get("external_id")
            if not ext_id:
                continue

            existing = db.query(EconomicEvent).filter(EconomicEvent.external_id == ext_id).first()
            if not existing:
                # Insert new event
                db.add(EconomicEvent(
                    external_id=ext_id,
                    currency=ev["currency"],
                    event_title=ev["event_title"],
                    impact_level=ev["impact_level"],
                    scheduled_at=ev["scheduled_at"],
                    actual_value=ev.get("actual_value"),
                    forecast_value=ev.get("forecast_value"),
                    previous_value=ev.get("previous_value"),
                    sentiment_impact=ev.get("sentiment_impact"),
                ))
                updated_count += 1
            else:
                # Upsert: update any changed fields
                changed = False
                new_actual = ev.get("actual_value")
                new_forecast = ev.get("forecast_value")
                new_prev = ev.get("previous_value")

                if new_actual is not None and existing.actual_value != new_actual:
                    existing.actual_value = new_actual
                    changed = True
                if new_forecast is not None and existing.forecast_value != new_forecast:
                    existing.forecast_value = new_forecast
                    changed = True
                if new_prev is not None and existing.previous_value != new_prev:
                    existing.previous_value = new_prev
                    changed = True

                if changed:
                    updated_count += 1

        if updated_count > 0:
            db.commit()
            logger.info(f"Upserted {updated_count} economic calendar events from ForexFactory.")
        return updated_count

    _last_news_fetch_time: float = 0.0
    _last_calendar_fetch_time: float = 0.0

    @staticmethod
    async def auto_refresh_if_stale(db: Session, symbol: str = "XAUUSD", max_age_seconds: int = 45) -> int:
        """
        Checks if news was fetched more than max_age_seconds ago (default 45s).
        If so, automatically triggers a fresh news ingestion from all global feeds.
        """
        import time
        now_ts = time.time()
        if (now_ts - IngestionService._last_news_fetch_time) < max_age_seconds:
            return 0

        IngestionService._last_news_fetch_time = now_ts
        try:
            return await IngestionService.ingest_latest_news(db, symbol)
        except Exception as e:
            logger.warning(f"Auto-refresh news failed: {e}")
            return 0

    @staticmethod
    async def auto_refresh_calendar_if_stale(db: Session, max_age_seconds: int = 90) -> int:
        """
        Checks if calendar was fetched more than max_age_seconds ago (default 90s).
        If so, automatically syncs released actual values and upcoming events.
        """
        import time
        now_ts = time.time()
        if (now_ts - IngestionService._last_calendar_fetch_time) < max_age_seconds:
            return 0

        IngestionService._last_calendar_fetch_time = now_ts
        try:
            return await IngestionService.ingest_latest_calendar(db)
        except Exception as e:
            logger.warning(f"Auto-refresh calendar failed: {e}")
            return 0
