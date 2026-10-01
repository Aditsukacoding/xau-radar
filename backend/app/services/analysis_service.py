import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
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
    @staticmethod
    async def get_or_generate_analysis(
        db: Session,
        symbol: str = "XAUUSD",
        force_refresh: bool = False,
    ) -> AnalysisReport:
        """
        Retrieves the latest persistent analysis report from DB, or triggers a fresh synthesis
        ONLY when:
        1. Force refresh is requested by user.
        2. No active setup exists in DB.
        3. The active setup HIT STOP LOSS (SL) -> Old structure invalidated, AI searches for a new zone.
        4. The active setup HIT FULL TAKE PROFIT 2 (TP2) -> Target completed, AI searches for next opportunity.
        5. Setup age exceeds 18 hours (expired daily structure).

        Otherwise, the setup (Entry, SL, TP) STAYS CONSISTENT AND FIXED as price oscillates.
        """
        provider = get_data_provider()
        price_snapshot = await provider.get_latest_price(symbol)
        curr_price = float(price_snapshot.get("current_price", 0.0))

        if not force_refresh:
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
                    # A. Hit Stop Loss?
                    if curr_price >= sl:
                        should_regenerate = True
                        reason = f"Harga (${curr_price:.2f}) menembus Stop Loss (${sl:.2f}). Setup SELL dibatalkan, AI mencari zona entry baru."
                    # B. Hit TP2 (Full Target)?
                    elif curr_price <= tp2 and tp2 > 0:
                        should_regenerate = True
                        reason = f"Harga (${curr_price:.2f}) mencapai Target TP2 (${tp2:.2f}). Setup profit maksimal selesai, AI mencari peluang baru."
                    # C. Hit TP1? (Partial lock 50% & move SL to BEP, KEEP setup parameters!)
                    elif curr_price <= tp1 and tp1 > 0:
                        setup["status"] = "RUNNING_TP1_HIT"
                        setup["status_message"] = (
                            f"TP1 ${tp1:.2f} Tercapai (+{setup.get('reward_tp1_pips', 40):.0f} pips). "
                            f"Kunci 50% profit & SL aman di BEP (${entry_p:.2f}). Sisa lot running ke TP2 ${tp2:.2f}."
                        )
                        latest.trade_setup_json = json.dumps(setup)
                        db.commit()
                        return latest
                    # D. Normal Floating - KEEP SETUP FIXED!
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
                            reason = "Setup SELL telah aktif lebih dari 18 jam. Memperbarui struktur harian."

                # --- 2. EVALUATE BUY SETUP ---
                elif action == "BUY" and entry_p > 0 and sl > 0:
                    # A. Hit Stop Loss?
                    if curr_price <= sl:
                        should_regenerate = True
                        reason = f"Harga (${curr_price:.2f}) menembus Stop Loss (${sl:.2f}). Setup BUY dibatalkan, AI mencari zona entry baru."
                    # B. Hit TP2 (Full Target)?
                    elif curr_price >= tp2 and tp2 > 0:
                        should_regenerate = True
                        reason = f"Harga (${curr_price:.2f}) mencapai Target TP2 (${tp2:.2f}). Setup profit maksimal selesai, AI mencari peluang baru."
                    # C. Hit TP1? (Partial lock 50% & move SL to BEP, KEEP setup parameters!)
                    elif curr_price >= tp1 and tp1 > 0:
                        setup["status"] = "RUNNING_TP1_HIT"
                        setup["status_message"] = (
                            f"TP1 ${tp1:.2f} Tercapai (+{setup.get('reward_tp1_pips', 40):.0f} pips). "
                            f"Kunci 50% profit & SL aman di BEP (${entry_p:.2f}). Sisa lot running ke TP2 ${tp2:.2f}."
                        )
                        latest.trade_setup_json = json.dumps(setup)
                        db.commit()
                        return latest
                    # D. Normal Floating - KEEP SETUP FIXED!
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
                            reason = "Setup BUY telah aktif lebih dari 18 jam. Memperbarui struktur harian."

                # --- 3. EVALUATE WAIT SETUP ---
                else:
                    if age_hours < 0.5:
                        return latest
                    should_regenerate = True
                    reason = "Memperbarui evaluasi breakout/breakdown pasar."

                if not should_regenerate:
                    return latest
                else:
                    logger.info(f"[TradeSetupLifecycle] Regenerating setup for {symbol}: {reason}")

        return await AnalysisService.generate_fresh_analysis(db, symbol)

    @staticmethod
    async def generate_fresh_analysis(db: Session, symbol: str = "XAUUSD") -> AnalysisReport:
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
