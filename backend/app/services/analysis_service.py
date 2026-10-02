import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.analysis_report import AnalysisReport
from app.models.price_candle import PriceCandle
from app.models.economic_event import EconomicEvent
from app.models.news_article import NewsArticle
from app.providers import get_data_provider
from app.services.technical_calc import TechnicalCalculator
from app.providers.ai_engine import AIAgentEngine
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnalysisService:
    _regen_lock = asyncio.Lock()

    @classmethod
    async def _safe_background_regeneration(cls, symbol: str = "XAUUSD"):
        """
        Executes AI market bias synthesis safely in the background with an independent
        database session and lock to ensure HTTP GET endpoints are never blocked.
        """
        if cls._regen_lock.locked():
            logger.info(f"[AnalysisService] Background AI regeneration for {symbol} already running, skipping duplicate trigger.")
            return

        async with cls._regen_lock:
            from app.core.database import SessionLocal
            db = SessionLocal()
            try:
                logger.info(f"[AnalysisService] Starting background AI market bias synthesis for {symbol}...")
                await cls.generate_fresh_analysis(db, symbol=symbol)
                logger.info(f"[AnalysisService] Background AI market bias synthesis finished successfully for {symbol}!")
            except Exception as e:
                logger.error(f"[AnalysisService] Background AI regeneration error: {e}", exc_info=True)
            finally:
                db.close()

    @classmethod
    async def _generate_instant_baseline(cls, db: Session, symbol: str = "XAUUSD") -> AnalysisReport:
        """
        Generates an instant quantitative heuristic report in sub-50ms when database
        has zero reports, ensuring no user ever waits or sees a freezing spinner.
        """
        provider = get_data_provider()

        # 1. Fetch candles
        candles_db = (
            db.query(PriceCandle)
            .filter(PriceCandle.symbol == symbol, PriceCandle.timeframe == "1h")
            .order_by(PriceCandle.timestamp.asc())
            .all()
        )
        if not candles_db:
            raw_candles = await provider.get_price_candles(symbol=symbol, timeframe="1h", count=60)
            candles_list = raw_candles
        else:
            candles_list = [
                {
                    "timestamp": c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in candles_db
            ]

        tech_data = TechnicalCalculator.calculate_indicators(candles_list)
        price_snapshot = await provider.get_latest_price(symbol)
        curr_price = float(price_snapshot.get("current_price", 4150.0))

        # 2. Events & News
        now = datetime.now(timezone.utc)
        events_db = (
            db.query(EconomicEvent)
            .filter(EconomicEvent.scheduled_at >= now)
            .order_by(EconomicEvent.scheduled_at.asc())
            .limit(5)
            .all()
        )
        events_data = [
            {
                "event_title": e.event_title,
                "impact_level": e.impact_level,
                "scheduled_at": e.scheduled_at.isoformat(),
                "forecast_value": e.forecast_value,
                "previous_value": e.previous_value,
                "sentiment_impact": e.sentiment_impact,
            }
            for e in events_db
        ]

        news_db = (
            db.query(NewsArticle)
            .filter(NewsArticle.symbol == symbol)
            .order_by(desc(NewsArticle.published_at))
            .limit(5)
            .all()
        )
        news_data = [
            {
                "title": n.title,
                "source": n.source,
                "summary": n.summary,
                "sentiment_label": n.sentiment_label,
                "sentiment_score": n.sentiment_score,
            }
            for n in news_db
        ]

        # 3. Instant quantitative synthesis (sub-millisecond)
        raw_heuristic = AIAgentEngine._heuristic_synthesis(
            symbol=symbol,
            price_snapshot=price_snapshot,
            technical_data=tech_data,
            economic_events=events_data,
            news_articles=news_data,
        )
        sanitized = AIAgentEngine._sanitize_and_validate_trade_setup(
            raw_heuristic,
            curr_price=curr_price,
            technical_data=tech_data,
            economic_events=events_data,
            news_articles=news_data,
        )

        report = AnalysisReport(
            symbol=symbol,
            timeframe="1h",
            bias=sanitized.get("bias", "BULLISH"),
            confidence_score=sanitized.get("confidence_score", 70),
            summary=sanitized.get("summary", ""),
            fundamental_notes=sanitized.get("fundamental_notes", ""),
            geopolitical_notes=sanitized.get("geopolitical_notes", ""),
            technical_notes=sanitized.get("technical_notes", ""),
            key_levels_json=json.dumps(sanitized.get("key_levels", {"support": [], "resistance": []})),
            trade_setup_json=json.dumps(sanitized.get("trade_setup", {})),
            risk_factors_json=json.dumps(sanitized.get("risk_factors", [])),
            sources_json=json.dumps(sanitized.get("sources", [])),
            disclaimer=settings.MANDATORY_DISCLAIMER,
            created_at=datetime.now(timezone.utc),
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        logger.info(f"[AnalysisService] Instant quantitative baseline report generated for {symbol} (<50ms).")
        return report

    @classmethod
    async def get_or_generate_analysis(
        cls,
        db: Session,
        symbol: str = "XAUUSD",
        force_refresh: bool = False,
    ) -> AnalysisReport:
        """
        Retrieves the latest persistent analysis report from DB with INSTANT sub-20ms response time.
        Any required regeneration (SL hit, TP2 hit, or expiration) is offloaded to a background task
        so user GET requests are NEVER blocked by slow external AI API calls.
        """
        if force_refresh:
            return await cls.generate_fresh_analysis(db, symbol)

        provider = get_data_provider()
        price_snapshot = await provider.get_latest_price(symbol)
        curr_price = float(price_snapshot.get("current_price", 0.0))

        latest = (
            db.query(AnalysisReport)
            .filter(AnalysisReport.symbol == symbol)
            .order_by(desc(AnalysisReport.created_at))
            .first()
        )

        if latest and curr_price > 0:
            now = datetime.now(timezone.utc)
            created = latest.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)

            age_hours = (now - created).total_seconds() / 3600.0

            try:
                setup = json.loads(latest.trade_setup_json or "{}")
            except Exception:
                setup = {}

            action = setup.get("action", "WAIT")
            entry_p = float(setup.get("entry_price", 0.0))
            sl = float(setup.get("stop_loss", 0.0))
            tp1 = float(setup.get("take_profit_1", 0.0))
            tp2 = float(setup.get("take_profit_2", 0.0))

            should_regenerate = False
            reason = ""

            # --- 1. EVALUATE SELL SETUP ---
            if action == "SELL" and entry_p > 0 and sl > 0:
                if curr_price >= sl:
                    should_regenerate = True
                    reason = f"Harga (${curr_price:.2f}) menembus Stop Loss (${sl:.2f})."
                elif curr_price <= tp2 and tp2 > 0:
                    should_regenerate = True
                    reason = f"Harga (${curr_price:.2f}) mencapai Target TP2 (${tp2:.2f})."
                elif curr_price <= tp1 and tp1 > 0:
                    setup["status"] = "RUNNING_TP1_HIT"
                    setup["status_message"] = (
                        f"TP1 ${tp1:.2f} Tercapai (+{setup.get('reward_tp1_pips', 40):.0f} pips). "
                        f"Kunci 50% profit & SL aman di BEP (${entry_p:.2f}). Sisa lot running ke TP2 ${tp2:.2f}."
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest
                else:
                    if age_hours < 18.0:
                        pips_diff = round((entry_p - curr_price) * 10, 1)
                        floating_str = f"+{pips_diff:.1f} pips" if pips_diff >= 0 else f"{pips_diff:.1f} pips"
                        setup["status"] = "ACTIVE"
                        setup["status_message"] = f"Setup SELL Terkunci (Entry: ${entry_p:.2f} | Floating: {floating_str}). Menunggu Target/SL."
                        latest.trade_setup_json = json.dumps(setup)
                        db.commit()
                        return latest
                    else:
                        should_regenerate = True
                        reason = "Setup SELL telah aktif lebih dari 18 jam."

            # --- 2. EVALUATE BUY SETUP ---
            elif action == "BUY" and entry_p > 0 and sl > 0:
                if curr_price <= sl:
                    should_regenerate = True
                    reason = f"Harga (${curr_price:.2f}) menembus Stop Loss (${sl:.2f})."
                elif curr_price >= tp2 and tp2 > 0:
                    should_regenerate = True
                    reason = f"Harga (${curr_price:.2f}) mencapai Target TP2 (${tp2:.2f})."
                elif curr_price >= tp1 and tp1 > 0:
                    setup["status"] = "RUNNING_TP1_HIT"
                    setup["status_message"] = (
                        f"TP1 ${tp1:.2f} Tercapai (+{setup.get('reward_tp1_pips', 40):.0f} pips). "
                        f"Kunci 50% profit & SL aman di BEP (${entry_p:.2f}). Sisa lot running ke TP2 ${tp2:.2f}."
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest
                else:
                    if age_hours < 18.0:
                        pips_diff = round((curr_price - entry_p) * 10, 1)
                        floating_str = f"+{pips_diff:.1f} pips" if pips_diff >= 0 else f"{pips_diff:.1f} pips"
                        setup["status"] = "ACTIVE"
                        setup["status_message"] = f"Setup BUY Terkunci (Entry: ${entry_p:.2f} | Floating: {floating_str}). Menunggu Target/SL."
                        latest.trade_setup_json = json.dumps(setup)
                        db.commit()
                        return latest
                    else:
                        should_regenerate = True
                        reason = "Setup BUY telah aktif lebih dari 18 jam."

            # --- 3. EVALUATE WAIT SETUP ---
            else:
                if age_hours >= 0.5:
                    should_regenerate = True
                    reason = "Memperbarui evaluasi breakout/breakdown pasar (30m expired)."

            if should_regenerate:
                logger.info(f"[TradeSetupLifecycle] Scheduling background AI refresh for {symbol}: {reason}")
                asyncio.create_task(cls._safe_background_regeneration(symbol))

            # Non-blocking: Return the latest valid report immediately
            return latest

        # If database is completely empty:
        logger.info(f"[AnalysisService] Database empty for {symbol}. Creating instant baseline and queuing background AI synthesis...")
        baseline = await cls._generate_instant_baseline(db, symbol)
        asyncio.create_task(cls._safe_background_regeneration(symbol))
        return baseline

    @classmethod
    async def generate_fresh_analysis(cls, db: Session, symbol: str = "XAUUSD") -> AnalysisReport:
        provider = get_data_provider()

        # 1. Fetch candles from DB or provider
        candles_db = (
            db.query(PriceCandle)
            .filter(PriceCandle.symbol == symbol, PriceCandle.timeframe == "1h")
            .order_by(PriceCandle.timestamp.asc())
            .all()
        )
        if not candles_db:
            raw_candles = await provider.get_price_candles(symbol=symbol, timeframe="1h", count=60)
            candles_list = raw_candles
        else:
            candles_list = [
                {
                    "timestamp": c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in candles_db
            ]

        # 2. Compute technical indicators
        tech_data = TechnicalCalculator.calculate_indicators(candles_list)

        # 3. Get price snapshot
        price_snapshot = await provider.get_latest_price(symbol)

        # 4. Fetch fundamental & geopolitical inputs from DB or provider
        now = datetime.now(timezone.utc)
        events_db = (
            db.query(EconomicEvent)
            .filter(EconomicEvent.scheduled_at >= now)
            .order_by(EconomicEvent.scheduled_at.asc())
            .limit(5)
            .all()
        )
        if not events_db:
            raw_events = await provider.get_economic_calendar()
            events_data = raw_events
        else:
            events_data = [
                {
                    "event_title": e.event_title,
                    "impact_level": e.impact_level,
                    "scheduled_at": e.scheduled_at.isoformat(),
                    "forecast_value": e.forecast_value,
                    "previous_value": e.previous_value,
                    "sentiment_impact": e.sentiment_impact,
                }
                for e in events_db
            ]

        news_db = (
            db.query(NewsArticle)
            .filter(NewsArticle.symbol == symbol)
            .order_by(desc(NewsArticle.published_at))
            .limit(5)
            .all()
        )
        if not news_db:
            raw_news = await provider.get_news_articles(symbol)
            news_data = raw_news
        else:
            news_data = [
                {
                    "title": n.title,
                    "source": n.source,
                    "summary": n.summary,
                    "sentiment_label": n.sentiment_label,
                    "sentiment_score": n.sentiment_score,
                }
                for n in news_db
            ]

        # 5. Call AI Engine for synthesis
        ai_res = await AIAgentEngine.synthesize_market_bias(
            symbol=symbol,
            price_snapshot=price_snapshot,
            technical_data=tech_data,
            economic_events=events_data,
            news_articles=news_data,
        )

        # 6. Store report in database
        report = AnalysisReport(
            symbol=symbol,
            timeframe="1h",
            bias=ai_res.get("bias", "NEUTRAL"),
            confidence_score=ai_res.get("confidence_score", 65),
            summary=ai_res.get("summary", ""),
            fundamental_notes=ai_res.get("fundamental_notes", ""),
            geopolitical_notes=ai_res.get("geopolitical_notes", ""),
            technical_notes=ai_res.get("technical_notes", ""),
            key_levels_json=json.dumps(ai_res.get("key_levels", {"support": [], "resistance": []})),
            trade_setup_json=json.dumps(ai_res.get("trade_setup", {})),
            risk_factors_json=json.dumps(ai_res.get("risk_factors", [])),
            sources_json=json.dumps(ai_res.get("sources", [])),
            disclaimer=settings.MANDATORY_DISCLAIMER,
            created_at=datetime.now(timezone.utc),
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        return report
