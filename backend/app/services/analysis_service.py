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
    async def _fetch_mtf_indicators(
        cls,
        db: Session,
        symbol: str,
        curr_price: float,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetches Multi-Timeframe candles (5m, 15m, 1h) from DB or live provider,
        anchors the latest bar to real-time spot price, and calculates full scalping indicators.
        """
        provider = get_data_provider()
        mtf_results: Dict[str, Dict[str, Any]] = {}

        async def load_tf(tf: str, count: int) -> List[Dict[str, Any]]:
            candles_db = (
                db.query(PriceCandle)
                .filter(PriceCandle.symbol == symbol, PriceCandle.timeframe == tf)
                .order_by(desc(PriceCandle.timestamp))
                .limit(count)
                .all()
            )
            need_live = len(candles_db) < 20
            if not need_live and candles_db:
                latest_ts = candles_db[0].timestamp
                if latest_ts.tzinfo is None:
                    latest_ts = latest_ts.replace(tzinfo=timezone.utc)
                max_stale = 300 if tf == "5m" else (900 if tf == "15m" else 1800)
                if (datetime.now(timezone.utc) - latest_ts).total_seconds() > max_stale:
                    need_live = True

            if need_live:
                try:
                    raw = await provider.get_price_candles(symbol=symbol, timeframe=tf, count=count)
                    if raw:
                        candles_list = sorted(raw, key=lambda c: c["timestamp"])
                    else:
                        candles_list = []
                except Exception as e:
                    logger.warning(f"[AnalysisService] Live {tf} fetch failed, using DB cache: {e}")
                    candles_list = [
                        {
                            "timestamp": c.timestamp,
                            "open": c.open,
                            "high": c.high,
                            "low": c.low,
                            "close": c.close,
                            "volume": c.volume,
                        }
                        for c in reversed(candles_db)
                    ]
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
                    for c in reversed(candles_db)
                ]

            if candles_list and curr_price > 500.0:
                last = dict(candles_list[-1])
                last["close"] = curr_price
                last["high"] = max(float(last["high"]), curr_price)
                last["low"] = min(float(last["low"]), curr_price)
                candles_list[-1] = last

            return candles_list

        c5, c15, c1h = await asyncio.gather(
            load_tf("5m", 60),
            load_tf("15m", 60),
            load_tf("1h", 60),
        )

        mtf_results["1h"] = TechnicalCalculator.calculate_indicators(c1h)
        mtf_results["15m"] = TechnicalCalculator.calculate_indicators(c15 if len(c15) >= 15 else c1h)
        mtf_results["5m"] = TechnicalCalculator.calculate_indicators(c5 if len(c5) >= 15 else (c15 if len(c15) >= 15 else c1h))
        return mtf_results

    @classmethod
    def _load_events_and_news(cls, db: Session, symbol: str):
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
        return events_data, news_data

    @classmethod
    async def _generate_instant_baseline(cls, db: Session, symbol: str = "XAUUSD") -> AnalysisReport:
        """
        Generates a fast quantitative M5/M15/H1 scalping baseline report (SL + TP1 + TP2 + TP3)
        used during startup seeding or if external LLM endpoints time out.
        """
        provider = get_data_provider()
        price_snapshot = await provider.get_latest_price(symbol)
        curr_price = float(price_snapshot.get("current_price", 3560.0))

        mtf_tech = await cls._fetch_mtf_indicators(db, symbol, curr_price)
        h1_tech = mtf_tech["1h"]
        m15_tech = mtf_tech["15m"]
        m5_tech = mtf_tech["5m"]
        events_data, news_data = cls._load_events_and_news(db, symbol)

        raw_heuristic = AIAgentEngine._heuristic_synthesis(
            symbol=symbol,
            price_snapshot=price_snapshot,
            technical_data=h1_tech,
            economic_events=events_data,
            news_articles=news_data,
            m15_data=m15_tech,
            m5_data=m5_tech,
        )
        sanitized = AIAgentEngine._sanitize_and_validate_trade_setup(
            raw_heuristic,
            curr_price=curr_price,
            technical_data=h1_tech,
            m15_data=m15_tech,
            m5_data=m5_tech,
            economic_events=events_data,
            news_articles=news_data,
        )

        report = AnalysisReport(
            symbol=symbol,
            timeframe="15m",
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
        logger.info(f"[AnalysisService] Quantitative MTF scalping baseline generated for {symbol}.")
        return report

    @classmethod
    async def get_or_generate_analysis(
        cls,
        db: Session,
        symbol: str = "XAUUSD",
        force_refresh: bool = False,
    ) -> AnalysisReport:
        """
        Retrieves the active direct-scalping setup from DB and tracks live 3-tier TP progression:
        - ACTIVE -> RUNNING_TP1_HIT (SL→BEP) -> RUNNING_TP2_HIT (SL→TP1) -> TP3/SL triggers fresh AI setup.
        - Auto-regenerates cleanly (serverless-safe, awaited with timeout) whenever setup hits SL, hits TP3,
          lacks TP3 schema, drifts stale, or exceeds 3-hour scalping freshness window.
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

            action = str(setup.get("action", "WAIT")).upper()
            entry_p = float(setup.get("entry_price", 0.0) or 0.0)
            sl = float(setup.get("stop_loss", 0.0) or 0.0)
            tp1 = float(setup.get("take_profit_1", 0.0) or 0.0)
            tp2 = float(setup.get("take_profit_2", 0.0) or 0.0)
            tp3 = float(setup.get("take_profit_3", 0.0) or 0.0)

            should_regenerate = False
            reason = ""

            # Force upgrade legacy pre-TP3 setups immediately
            if tp3 <= 0 or entry_p <= 0 or sl <= 0:
                should_regenerate = True
                reason = "Upgrade skema setup ke Direct Scalping TP1/TP2/TP3."

            # --- 1. EVALUATE SELL SCALP SETUP ---
            elif action == "SELL":
                if curr_price >= sl:
                    should_regenerate = True
                    reason = f"Harga (${curr_price:.2f}) menyentuh SL (${sl:.2f})."
                elif curr_price <= tp3:
                    should_regenerate = True
                    reason = f"Target Maksimal TP3 (${tp3:.2f}) Tercapai! Memperbarui setup baru."
                elif curr_price <= tp2 and tp2 > 0:
                    setup["status"] = "RUNNING_TP2_HIT"
                    setup["status_message"] = (
                        f"TP2 ${tp2:.2f} Hit (+{setup.get('reward_tp2_pips', 70):.0f} pips)! "
                        f"Kunci 80% total lot & geser SL ke TP1 (${tp1:.2f}). Sisa 20% runner ke TP3 ${tp3:.2f}."
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest
                elif curr_price <= tp1 and tp1 > 0:
                    setup["status"] = "RUNNING_TP1_HIT"
                    setup["status_message"] = (
                        f"TP1 ${tp1:.2f} Hit (+{setup.get('reward_tp1_pips', 35):.0f} pips)! "
                        f"Kunci 40% lot & geser SL ke BEP (${entry_p:.2f}). Lanjut ke TP2 ${tp2:.2f} / TP3 ${tp3:.2f}."
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest
                elif age_hours >= 3.0:
                    should_regenerate = True
                    reason = "Setup scalping SELL melebihi jendela 3 jam — kalibrasi sesi baru."
                else:
                    pips_diff = round((entry_p - curr_price) * 10.0, 1)
                    floating_str = f"+{pips_diff:.1f}" if pips_diff >= 0 else f"{pips_diff:.1f}"
                    setup["status"] = "ACTIVE"
                    setup["status_message"] = (
                        f"{setup.get('action_label', 'SELL SCALP')} • Acuan ${entry_p:.2f} | Floating {floating_str} pips"
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest

            # --- 2. EVALUATE BUY SCALP SETUP ---
            elif action == "BUY":
                if curr_price <= sl:
                    should_regenerate = True
                    reason = f"Harga (${curr_price:.2f}) menyentuh SL (${sl:.2f})."
                elif curr_price >= tp3:
                    should_regenerate = True
                    reason = f"Target Maksimal TP3 (${tp3:.2f}) Tercapai! Memperbarui setup baru."
                elif curr_price >= tp2 and tp2 > 0:
                    setup["status"] = "RUNNING_TP2_HIT"
                    setup["status_message"] = (
                        f"TP2 ${tp2:.2f} Hit (+{setup.get('reward_tp2_pips', 70):.0f} pips)! "
                        f"Kunci 80% total lot & geser SL ke TP1 (${tp1:.2f}). Sisa 20% runner ke TP3 ${tp3:.2f}."
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest
                elif curr_price >= tp1 and tp1 > 0:
                    setup["status"] = "RUNNING_TP1_HIT"
                    setup["status_message"] = (
                        f"TP1 ${tp1:.2f} Hit (+{setup.get('reward_tp1_pips', 35):.0f} pips)! "
                        f"Kunci 40% lot & geser SL ke BEP (${entry_p:.2f}). Lanjut ke TP2 ${tp2:.2f} / TP3 ${tp3:.2f}."
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest
                elif age_hours >= 3.0:
                    should_regenerate = True
                    reason = "Setup scalping BUY melebihi jendela 3 jam — kalibrasi sesi baru."
                else:
                    pips_diff = round((curr_price - entry_p) * 10.0, 1)
                    floating_str = f"+{pips_diff:.1f}" if pips_diff >= 0 else f"{pips_diff:.1f}"
                    setup["status"] = "ACTIVE"
                    setup["status_message"] = (
                        f"{setup.get('action_label', 'BUY SCALP')} • Acuan ${entry_p:.2f} | Floating {floating_str} pips"
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest

            # --- 3. EVALUATE WAIT / NEWS GUARD SETUP ---
            else:
                if age_hours >= 0.25 or abs(curr_price - entry_p) >= 3.5:
                    should_regenerate = True
                    reason = "Evaluasi ulang kondisi pasar pasca News Guard / konsolidasi."

            if should_regenerate:
                logger.info(f"[TradeSetupLifecycle] Regenerating direct scalping setup for {symbol}: {reason}")
                try:
                    return await asyncio.wait_for(cls.generate_fresh_analysis(db, symbol), timeout=14.0)
                except Exception as e:
                    logger.warning(f"[AnalysisService] Fresh AI synthesis timed out/failed ({e}), falling back to instant baseline.")
                    return await cls._generate_instant_baseline(db, symbol)

            return latest

        # Database empty -> run fresh AI synthesis directly (serverless-safe) with fast fallback
        logger.info(f"[AnalysisService] Database empty for {symbol}. Running fresh scalping analysis...")
        try:
            return await asyncio.wait_for(cls.generate_fresh_analysis(db, symbol), timeout=14.0)
        except Exception as e:
            logger.warning(f"[AnalysisService] Initial AI synthesis failed/timed out ({e}), using instant MTF baseline.")
            return await cls._generate_instant_baseline(db, symbol)

    @classmethod
    async def generate_fresh_analysis(cls, db: Session, symbol: str = "XAUUSD") -> AnalysisReport:
        provider = get_data_provider()

        # 1. Get live spot price snapshot
        price_snapshot = await provider.get_latest_price(symbol)
        curr_price = float(price_snapshot.get("current_price", 3560.0))

        # 2. Fetch Multi-Timeframe technical context (M5 + M15 + H1 + ATR + Fractal Swings + Session)
        mtf_tech = await cls._fetch_mtf_indicators(db, symbol, curr_price)
        h1_tech = mtf_tech["1h"]

        # 3. Fetch fundamental & geopolitical inputs
        events_data, news_data = cls._load_events_and_news(db, symbol)
        if not events_data:
            try:
                events_data = await provider.get_economic_calendar()
            except Exception:
                events_data = []
        if not news_data:
            try:
                news_data = await provider.get_news_articles(symbol)
            except Exception:
                news_data = []

        # 4. Call AI Engine (Claude Sonnet/Haiku -> Gemini -> OpenRouter -> Quantitative MTF Scalping Engine)
        ai_res = await AIAgentEngine.synthesize_market_bias(
            symbol=symbol,
            price_snapshot=price_snapshot,
            technical_data=h1_tech,
            economic_events=events_data,
            news_articles=news_data,
            mtf_technical=mtf_tech,
        )

        # 5. Store report in database
        report = AnalysisReport(
            symbol=symbol,
            timeframe="15m",
            bias=ai_res.get("bias", "BULLISH"),
            confidence_score=ai_res.get("confidence_score", 72),
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
