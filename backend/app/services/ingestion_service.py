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

        # Fast path for permanent PostgreSQL (Neon/Supabase): if XAUUSD instrument already exists,
        # the database is already seeded — skip 5 extra COUNT(*) round-trips on every serverless cold start!
        xau = db.query(Instrument).filter(Instrument.symbol == "XAUUSD").first()
        if xau:
            return

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
        try:
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
        except Exception as e:
            logger.warning(f"Initial calendar seed skipped/failed: {e}")
            db.rollback()

        # 3. Seed News Articles
        try:
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
        except Exception as e:
            logger.warning(f"Initial news seed skipped/failed: {e}")
            db.rollback()

        # 4. Seed Candles for 15m, 1h, 1d
        try:
            candle_count = db.query(PriceCandle).filter(PriceCandle.symbol == "XAUUSD").count()
            if candle_count == 0:
                logger.info("Fetching real/initial candlestick price data...")
                for tf in ["15m", "1h", "1d"]:
                    try:
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
                    except Exception as ce:
                        logger.warning(f"Candle seed for {tf} failed: {ce}")
                        db.rollback()
        except Exception as e:
            logger.warning(f"Candle count check failed: {e}")

        # 5. Generate initial Analysis Report instantly (< 50ms)
        try:
            report_count = db.query(AnalysisReport).filter(AnalysisReport.symbol == "XAUUSD").count()
            if report_count == 0:
                logger.info("Generating instant quantitative baseline report (<50ms)...")
                await AnalysisService._generate_instant_baseline(db, symbol="XAUUSD")
        except Exception as e:
            logger.warning(f"Initial baseline report seed failed: {e}")

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
        logger.info(f"Syncing real live market data for {symbol}...")

        import asyncio
        # Sync 15m & 1h recent bars only (4h/1d fetched live on-demand; keeps Neon PostgreSQL sync <3s!)
        tfs = ["15m", "1h"]

        async def _safe(coro, fallback):
            try:
                return await asyncio.wait_for(coro, timeout=6.5)
            except Exception as e:
                logger.warning(f"[Sync] Live fetch skipped: {e}")
                return fallback

        # Fetch candles, news & calendar CONCURRENTLY
        results = await asyncio.gather(
            *[_safe(provider.get_price_candles(symbol=symbol, timeframe=tf, count=25), []) for tf in tfs],
            _safe(provider.get_news_articles(symbol=symbol, limit=15), []),
            _safe(provider.get_economic_calendar(), []),
        )
        tf_candles_list = results[:len(tfs)]
        raw_news = results[len(tfs)]
        raw_events = results[len(tfs) + 1]

        def _naive_utc(dt):
            if dt is None:
                return None
            return dt.astimezone(timezone.utc).replace(tzinfo=None) if getattr(dt, "tzinfo", None) else dt

        # 1. Upsert ONLY genuinely new or changed Candles using a SINGLE multi-row INSERT (1 TCP round-trip on pg8000!)
        from sqlalchemy import insert as sa_insert
        try:
            new_candle_dicts = []
            has_updates = False
            for tf, raw_candles in zip(tfs, tf_candles_list):
                if not raw_candles:
                    continue
                recent_raw = raw_candles[-15:]
                existing_rows = (
                    db.query(PriceCandle)
                    .filter(PriceCandle.symbol == symbol, PriceCandle.timeframe == tf)
                    .order_by(desc(PriceCandle.timestamp))
                    .limit(40)
                    .all()
                )
                existing_by_ts = {_naive_utc(r.timestamp): r for r in existing_rows}
                seen_new_ts = set(existing_by_ts.keys())
                for c in recent_raw:
                    c_key = _naive_utc(c["timestamp"])
                    if c_key is None:
                        continue
                    existing = existing_by_ts.get(c_key)
                    if existing is None:
                        if c_key in seen_new_ts:
                            continue
                        seen_new_ts.add(c_key)
                        new_candle_dicts.append({
                            "symbol": symbol,
                            "timeframe": tf,
                            "timestamp": c_key,
                            "open": float(c["open"]),
                            "high": float(c["high"]),
                            "low": float(c["low"]),
                            "close": float(c["close"]),
                            "volume": float(c.get("volume", 0.0) or 0.0),
                        })
                    else:
                        new_h = max(existing.high, float(c["high"]))
                        new_l = min(existing.low, float(c["low"]))
                        new_c = float(c["close"])
                        if abs(existing.close - new_c) >= 0.05 or abs(existing.high - new_h) >= 0.05 or abs(existing.low - new_l) >= 0.05:
                            existing.close = new_c
                            existing.high = new_h
                            existing.low = new_l
                            has_updates = True
            if new_candle_dicts:
                db.execute(sa_insert(PriceCandle).values(new_candle_dicts))
            if new_candle_dicts or has_updates:
                db.commit()
        except Exception as e:
            logger.warning(f"[Sync] Candle upsert skipped after error: {e}")
            db.rollback()

        # 2. Single multi-row INSERT for new News articles (1 SELECT + 1 INSERT)
        try:
            if raw_news:
                existing_titles = {
                    row[0] for row in db.query(NewsArticle.title).filter(NewsArticle.symbol == symbol).order_by(desc(NewsArticle.published_at)).limit(120).all()
                }
                new_news_dicts = []
                for nw in raw_news:
                    if nw["title"] not in existing_titles:
                        existing_titles.add(nw["title"])
                        new_news_dicts.append({
                            "symbol": symbol,
                            "title": nw["title"],
                            "source": nw["source"],
                            "url": nw.get("url"),
                            "summary": nw.get("summary"),
                            "sentiment_label": nw["sentiment_label"],
                            "sentiment_score": nw["sentiment_score"],
                            "published_at": _naive_utc(nw["published_at"]),
                            "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
                        })
                if new_news_dicts:
                    db.execute(sa_insert(NewsArticle).values(new_news_dicts))
                    db.commit()
        except Exception as e:
            logger.warning(f"[Sync] News ingest skipped after error: {e}")
            db.rollback()

        # 3. Single multi-row INSERT for new Calendar events (1 SELECT + 1 INSERT)
        try:
            if raw_events:
                existing_ext_ids = {
                    row[0] for row in db.query(EconomicEvent.external_id).filter(EconomicEvent.external_id.isnot(None)).all()
                }
                new_ev_dicts = []
                for ev in raw_events:
                    ext_id = ev.get("external_id")
                    if ext_id and ext_id not in existing_ext_ids:
                        existing_ext_ids.add(ext_id)
                        new_ev_dicts.append({
                            "external_id": ext_id,
                            "currency": ev["currency"],
                            "event_title": ev["event_title"],
                            "impact_level": ev["impact_level"],
                            "scheduled_at": _naive_utc(ev["scheduled_at"]),
                            "actual_value": ev.get("actual_value"),
                            "forecast_value": ev.get("forecast_value"),
                            "previous_value": ev.get("previous_value"),
                            "sentiment_impact": ev.get("sentiment_impact"),
                            "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
                        })
                if new_ev_dicts:
                    db.execute(sa_insert(EconomicEvent).values(new_ev_dicts))
                    db.commit()
        except Exception as e:
            logger.warning(f"[Sync] Calendar ingest skipped after error: {e}")
            db.rollback()

        # 4. Done — caller (endpoints_dashboard.trigger_full_live_sync) evaluates & returns locked setup once
        return None

    @staticmethod
    async def ingest_latest_news(db: Session, symbol: str = "XAUUSD") -> int:
        """
        Fetches breaking real-time news from multi-stream feeds and ingests any new articles.
        Returns count of newly ingested articles.
        """
        provider = get_data_provider()
        raw_news = await provider.get_news_articles(symbol=symbol, limit=45)
        new_count = 0

        # Prune legacy irrelevant articles (e.g. 'warning'/'warn' false positives before word-boundary filter)
        try:
            from app.providers.live_provider import LiveDataProvider
            existing_rows = (
                db.query(NewsArticle)
                .filter(NewsArticle.symbol == symbol.upper())
                .order_by(NewsArticle.published_at.desc())
                .limit(80)
                .all()
            )
            pruned = 0
            for row in existing_rows:
                if row.title and not LiveDataProvider._is_xau_relevant(row.title):
                    db.delete(row)
                    pruned += 1
            if pruned > 0:
                db.commit()
                logger.info(f"Pruned {pruned} legacy off-topic news articles.")
        except Exception:
            db.rollback()

        from sqlalchemy import insert as sa_insert

        def _naive(dt):
            if dt is None:
                return None
            return dt.astimezone(timezone.utc).replace(tzinfo=None) if getattr(dt, "tzinfo", None) else dt

        # Bulk-check existing titles & urls in 1 SELECT (eliminates 45 N+1 queries on Neon!)
        existing_pairs = (
            db.query(NewsArticle.title, NewsArticle.url)
            .filter(NewsArticle.symbol == symbol.upper())
            .order_by(desc(NewsArticle.published_at))
            .limit(200)
            .all()
        )
        seen_titles = {r[0] for r in existing_pairs if r[0]}
        seen_urls = {r[1] for r in existing_pairs if r[1]}
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        new_rows = []
        for nw in raw_news:
            t = nw.get("title")
            u = nw.get("url")
            if t in seen_titles or (u and u in seen_urls):
                continue
            seen_titles.add(t)
            if u:
                seen_urls.add(u)
            new_rows.append({
                "symbol": symbol.upper(),
                "title": t,
                "source": nw["source"],
                "url": u,
                "summary": nw.get("summary"),
                "sentiment_label": nw["sentiment_label"],
                "sentiment_score": nw["sentiment_score"],
                "published_at": _naive(nw["published_at"]),
                "created_at": now_naive,
            })

        if new_rows:
            try:
                db.execute(sa_insert(NewsArticle).values(new_rows))
                db.commit()
                new_count = len(new_rows)
                logger.info(f"Ingested {new_count} new breaking news articles into database.")
            except Exception as e:
                logger.warning(f"Bulk news insert skipped: {e}")
                db.rollback()
        return new_count

    @staticmethod
    async def ingest_latest_calendar(db: Session) -> int:
        """
        Fetches latest economic calendar events from ForexFactory and performs a bulk 1-SELECT upsert.
        """
        from sqlalchemy import insert as sa_insert

        def _naive(dt):
            if dt is None:
                return None
            return dt.astimezone(timezone.utc).replace(tzinfo=None) if getattr(dt, "tzinfo", None) else dt

        provider = get_data_provider()
        raw_events = await provider.get_economic_calendar()
        if not raw_events:
            return 0

        existing_rows = db.query(EconomicEvent).filter(EconomicEvent.external_id.isnot(None)).all()
        existing_map = {r.external_id: r for r in existing_rows}
        new_rows = []
        updated_count = 0
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

        for ev in raw_events:
            ext_id = ev.get("external_id")
            if not ext_id:
                continue
            existing = existing_map.get(ext_id)
            if existing is None:
                existing_map[ext_id] = True
                new_rows.append({
                    "external_id": ext_id,
                    "currency": ev["currency"],
                    "event_title": ev["event_title"],
                    "impact_level": ev["impact_level"],
                    "scheduled_at": _naive(ev["scheduled_at"]),
                    "actual_value": ev.get("actual_value"),
                    "forecast_value": ev.get("forecast_value"),
                    "previous_value": ev.get("previous_value"),
                    "sentiment_impact": ev.get("sentiment_impact"),
                    "created_at": now_naive,
                })
                updated_count += 1
            elif existing is not True:
                changed = False
                for field, key in (("actual_value", "actual_value"), ("forecast_value", "forecast_value"), ("previous_value", "previous_value")):
                    nv = ev.get(key)
                    if nv is not None and getattr(existing, field) != nv:
                        setattr(existing, field, nv)
                        changed = True
                if changed:
                    updated_count += 1

        try:
            if new_rows:
                db.execute(sa_insert(EconomicEvent).values(new_rows))
            if updated_count > 0:
                db.commit()
                logger.info(f"Upserted {updated_count} economic calendar events from ForexFactory.")
        except Exception as e:
            logger.warning(f"Bulk calendar upsert skipped: {e}")
            db.rollback()
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
