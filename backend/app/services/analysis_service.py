import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.analysis_report import AnalysisReport
from app.models.price_candle import PriceCandle
from app.models.economic_event import EconomicEvent
from app.models.news_article import NewsArticle
from app.providers import get_data_provider
from app.services.technical_calc import TechnicalCalculator
from app.services.macro_intelligence import MacroIntelligenceService
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
    ) -> Dict[str, Any]:
        """
        Fetches full 7-Timeframe OHLCV candles concurrently (1m, 5m, 15m, 30m, 1h, 4h, 1d),
        anchors the latest bar of every timeframe to live spot price, calculates full technical
        indicators per timeframe, and synthesizes cross-timeframe confluence zones.
        """
        provider = get_data_provider()
        tf_configs = [
            ("1m", 60, 60),
            ("5m", 60, 300),
            ("15m", 60, 900),
            ("30m", 60, 1800),
            ("1h", 60, 1800),
            ("4h", 60, 7200),
            ("1d", 60, 14400),
        ]

        async def load_tf(tf: str, count: int, max_stale: int) -> List[Dict[str, Any]]:
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
                if (datetime.now(timezone.utc) - latest_ts).total_seconds() > max_stale:
                    need_live = True

            if need_live:
                try:
                    raw = await provider.get_price_candles(symbol=symbol, timeframe=tf, count=count)
                    candles_list = sorted(raw, key=lambda c: c["timestamp"]) if raw else []
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

        fetched = await asyncio.gather(*[load_tf(tf, cnt, stale) for tf, cnt, stale in tf_configs])

        mtf_results: Dict[str, Any] = {}
        fallback_candles = fetched[4] if len(fetched[4]) >= 15 else (fetched[2] if len(fetched[2]) >= 15 else fetched[1])
        for (tf, _, _), c_list in zip(tf_configs, fetched):
            use_list = c_list if len(c_list) >= 15 else fallback_candles
            mtf_results[tf] = TechnicalCalculator.calculate_indicators(use_list)

        mtf_results["confluence"] = TechnicalCalculator.analyze_mtf_confluence(mtf_results, curr_price)
        mtf_results["_h1_candles"] = fetched[4] if len(fetched) > 4 else []
        return mtf_results

    @classmethod
    def _load_events_and_news(cls, db: Session, symbol: str):
        now = datetime.now(timezone.utc)
        # Load recently released events (last 14 days for Actual vs Forecast + Historical Reaction) + upcoming 7 days
        events_db = (
            db.query(EconomicEvent)
            .filter(
                EconomicEvent.scheduled_at >= (now - timedelta(days=14)),
                EconomicEvent.scheduled_at <= (now + timedelta(days=7)),
            )
            .order_by(EconomicEvent.scheduled_at.asc())
            .limit(40)
            .all()
        )
        events_data = [
            {
                "currency": e.currency,
                "event_title": e.event_title,
                "impact_level": e.impact_level,
                "scheduled_at": e.scheduled_at.isoformat(),
                "actual_value": e.actual_value,
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
            .limit(35)
            .all()
        )
        news_data = [
            {
                "title": n.title,
                "source": n.source,
                "summary": n.summary,
                "sentiment_label": n.sentiment_label,
                "sentiment_score": n.sentiment_score,
                "published_at": n.published_at.isoformat() if n.published_at else now.isoformat(),
            }
            for n in news_db
        ]
        return events_data, news_data

    @classmethod
    async def _build_macro_context(
        cls,
        events_data: List[Dict[str, Any]],
        news_data: List[Dict[str, Any]],
        h1_candles: List[Dict[str, Any]],
        intermarket: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        im = intermarket if intermarket is not None else await MacroIntelligenceService.fetch_intermarket_snapshot()
        all_events = list(events_data or [])
        released_usd = sum(1 for e in all_events if str(e.get("currency", "")).upper() == "USD" and e.get("actual_value"))
        if released_usd < 3:
            tv_past = await MacroIntelligenceService.fetch_recent_released_usd_events(days_back=14)
            if tv_past:
                all_events.extend(tv_past)
        fund_eval = MacroIntelligenceService.evaluate_fundamental_pillar(all_events, im)
        geo_eval = MacroIntelligenceService.analyze_geopolitical_and_macro_news(news_data, im)
        hist_eval = MacroIntelligenceService.analyze_historical_news_reactions(all_events, h1_candles)
        return {
            "intermarket": im,
            "fundamental": fund_eval,
            "geopolitical": geo_eval,
            "historical_reactions": hist_eval,
        }

    @classmethod
    async def _generate_instant_baseline(cls, db: Session, symbol: str = "XAUUSD") -> AnalysisReport:
        """
        Generates a fast quantitative 7-TF + Macro/Intermarket baseline report
        used during startup seeding or if external LLM endpoints time out.
        """
        provider = get_data_provider()
        price_snapshot = await provider.get_latest_price(symbol)
        curr_price = float(price_snapshot.get("current_price", 3560.0))

        mtf_tech, intermarket = await asyncio.gather(
            cls._fetch_mtf_indicators(db, symbol, curr_price),
            MacroIntelligenceService.fetch_intermarket_snapshot(),
        )
        h1_tech = mtf_tech["1h"]
        m15_tech = mtf_tech["15m"]
        m5_tech = mtf_tech["5m"]
        events_data, news_data = cls._load_events_and_news(db, symbol)
        macro_ctx = await cls._build_macro_context(
            events_data, news_data, mtf_tech.get("_h1_candles") or [], intermarket=intermarket
        )

        raw_heuristic = AIAgentEngine._heuristic_synthesis(
            symbol=symbol,
            price_snapshot=price_snapshot,
            technical_data=h1_tech,
            economic_events=events_data,
            news_articles=news_data,
            m15_data=m15_tech,
            m5_data=m5_tech,
            mtf_technical=mtf_tech,
            macro_context=macro_ctx,
        )
        sanitized = AIAgentEngine._sanitize_and_validate_trade_setup(
            raw_heuristic,
            curr_price=curr_price,
            technical_data=h1_tech,
            m15_data=m15_tech,
            m5_data=m5_tech,
            mtf_technical=mtf_tech,
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

            # Force upgrade legacy setups (pre-TP3, pre-7TF, pre-Sniper, or pre-KeyZone proof)
            risk_pips_val = float(setup.get("risk_pips", 0.0) or 0.0)
            tp1_pips_val = float(setup.get("reward_tp1_pips", 0.0) or 0.0)
            exec_type = str(setup.get("execution_type", "INSTANT")).upper()
            cur_status = str(setup.get("status", "ACTIVE")).upper()
            if (
                tp3 <= 0
                or entry_p <= 0
                or sl <= 0
                or not setup.get("mtf_overview")
                or not setup.get("entry_reasons")
                or not setup.get("zone_proof")
                or int(setup.get("setup_quality_score", 0) or 0) <= 0
                or (action in ("BUY", "SELL") and (risk_pips_val > 52.0 or risk_pips_val < 28.0 or tp1_pips_val < 55.0))
            ):
                should_regenerate = True
                reason = "Kalibrasi setup ke Key-Zone Sniper 7-TF (Zona Reaksi Asli, SL 30–50p, TP1 60p, & Bukti Zona)."

            # --- 1. EVALUATE SELL SCALP / KEY-ZONE LIMIT SETUP ---
            elif action == "SELL":
                if exec_type == "LIMIT" and cur_status == "PENDING_LIMIT":
                    if curr_price >= sl:
                        should_regenerate = True
                        reason = f"Harga (${curr_price:.2f}) menembus zona Supply/SL (${sl:.2f})."
                    elif curr_price >= (entry_p - 1.20):
                        # Limit Order filled! Transition to ACTIVE tracking
                        setup["status"] = "ACTIVE"
                        setup["status_message"] = (
                            f"LIMIT TERJEMPUT di ${entry_p:.2f}! Posisi SELL aktif • SL ${sl:.2f} | TP1 ${tp1:.2f} (+60p)"
                        )
                        latest.trade_setup_json = json.dumps(setup)
                        db.commit()
                        return latest
                    elif age_hours >= 4.0 or (tp3 > 0 and curr_price < tp3 - 10.0):
                        should_regenerate = True
                        reason = "Pending SELL LIMIT melewati jendela 4 jam atau harga menjauh — memperbarui Key Zone."
                    else:
                        dist_p = round((entry_p - curr_price) * 10.0, 1)
                        setup["zone_distance_pips"] = max(0.0, dist_p)
                        setup["status"] = "PENDING_LIMIT"
                        setup["status_message"] = (
                            f"Menunggu harga naik +{dist_p:.0f} pips ke Key Zone {setup.get('entry_zone', f'${entry_p:.2f}')} "
                            f"(SL -{risk_pips_val:.0f}p aman di luar tembok)"
                        )
                        latest.trade_setup_json = json.dumps(setup)
                        db.commit()
                        return latest
                elif curr_price >= sl:
                    should_regenerate = True
                    reason = f"Harga (${curr_price:.2f}) menyentuh SL (${sl:.2f})."
                elif curr_price <= tp3:
                    should_regenerate = True
                    reason = f"Target Maksimal TP3 (${tp3:.2f}) Tercapai! Memperbarui setup baru."
                elif curr_price <= tp2 and tp2 > 0:
                    setup["status"] = "RUNNING_TP2_HIT"
                    setup["status_message"] = (
                        f"TP2 ${tp2:.2f} Hit (+{setup.get('reward_tp2_pips', 100):.0f} pips)! "
                        f"Kunci 80% total lot & geser SL ke TP1 (${tp1:.2f}). Sisa 20% runner ke TP3 ${tp3:.2f}."
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest
                elif curr_price <= tp1 and tp1 > 0:
                    setup["status"] = "RUNNING_TP1_HIT"
                    setup["status_message"] = (
                        f"TP1 ${tp1:.2f} Hit (+{setup.get('reward_tp1_pips', 60):.0f} pips)! "
                        f"Kunci 40% lot & geser SL ke BEP (${entry_p:.2f}). Lanjut ke TP2 ${tp2:.2f} / TP3 ${tp3:.2f}."
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest
                elif age_hours >= 3.5:
                    should_regenerate = True
                    reason = "Setup aktif SELL melebihi jendela 3.5 jam — kalibrasi sesi baru."
                else:
                    pips_diff = round((entry_p - curr_price) * 10.0, 1)
                    floating_str = f"+{pips_diff:.1f}" if pips_diff >= 0 else f"{pips_diff:.1f}"
                    setup["status"] = "ACTIVE"
                    setup["status_message"] = (
                        f"Posisi SELL Aktif • Acuan ${entry_p:.2f} | Floating {floating_str} pips"
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest

            # --- 2. EVALUATE BUY SCALP / KEY-ZONE LIMIT SETUP ---
            elif action == "BUY":
                if exec_type == "LIMIT" and cur_status == "PENDING_LIMIT":
                    if curr_price <= sl:
                        should_regenerate = True
                        reason = f"Harga (${curr_price:.2f}) menembus zona Demand/SL (${sl:.2f})."
                    elif curr_price <= (entry_p + 1.20):
                        setup["status"] = "ACTIVE"
                        setup["status_message"] = (
                            f"LIMIT TERJEMPUT di ${entry_p:.2f}! Posisi BUY aktif • SL ${sl:.2f} | TP1 ${tp1:.2f} (+60p)"
                        )
                        latest.trade_setup_json = json.dumps(setup)
                        db.commit()
                        return latest
                    elif age_hours >= 4.0 or (tp3 > 0 and curr_price > tp3 + 10.0):
                        should_regenerate = True
                        reason = "Pending BUY LIMIT melewati jendela 4 jam atau harga menjauh — memperbarui Key Zone."
                    else:
                        dist_p = round((curr_price - entry_p) * 10.0, 1)
                        setup["zone_distance_pips"] = max(0.0, dist_p)
                        setup["status"] = "PENDING_LIMIT"
                        setup["status_message"] = (
                            f"Menunggu harga turun -{dist_p:.0f} pips ke Key Zone {setup.get('entry_zone', f'${entry_p:.2f}')} "
                            f"(SL -{risk_pips_val:.0f}p aman di luar tembok)"
                        )
                        latest.trade_setup_json = json.dumps(setup)
                        db.commit()
                        return latest
                elif curr_price <= sl:
                    should_regenerate = True
                    reason = f"Harga (${curr_price:.2f}) menyentuh SL (${sl:.2f})."
                elif curr_price >= tp3:
                    should_regenerate = True
                    reason = f"Target Maksimal TP3 (${tp3:.2f}) Tercapai! Memperbarui setup baru."
                elif curr_price >= tp2 and tp2 > 0:
                    setup["status"] = "RUNNING_TP2_HIT"
                    setup["status_message"] = (
                        f"TP2 ${tp2:.2f} Hit (+{setup.get('reward_tp2_pips', 100):.0f} pips)! "
                        f"Kunci 80% total lot & geser SL ke TP1 (${tp1:.2f}). Sisa 20% runner ke TP3 ${tp3:.2f}."
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest
                elif curr_price >= tp1 and tp1 > 0:
                    setup["status"] = "RUNNING_TP1_HIT"
                    setup["status_message"] = (
                        f"TP1 ${tp1:.2f} Hit (+{setup.get('reward_tp1_pips', 60):.0f} pips)! "
                        f"Kunci 40% lot & geser SL ke BEP (${entry_p:.2f}). Lanjut ke TP2 ${tp2:.2f} / TP3 ${tp3:.2f}."
                    )
                    latest.trade_setup_json = json.dumps(setup)
                    db.commit()
                    return latest
                elif age_hours >= 3.5:
                    should_regenerate = True
                    reason = "Setup aktif BUY melebihi jendela 3.5 jam — kalibrasi sesi baru."
                else:
                    pips_diff = round((curr_price - entry_p) * 10.0, 1)
                    floating_str = f"+{pips_diff:.1f}" if pips_diff >= 0 else f"{pips_diff:.1f}"
                    setup["status"] = "ACTIVE"
                    setup["status_message"] = (
                        f"Posisi BUY Aktif • Acuan ${entry_p:.2f} | Floating {floating_str} pips"
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

        # 2. Fetch 7-Timeframe technical indicators AND live Intermarket (DXY, US10Y, WTI) concurrently
        mtf_tech, intermarket = await asyncio.gather(
            cls._fetch_mtf_indicators(db, symbol, curr_price),
            MacroIntelligenceService.fetch_intermarket_snapshot(),
        )
        h1_tech = mtf_tech["1h"]

        # 3. Fetch fundamental & geopolitical inputs (recent released + upcoming)
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

        # 3b. Evaluate Numeric Actual-vs-Forecast Surprises, Historical News Reactions & Time-Decayed Geo Intelligence
        macro_ctx = await cls._build_macro_context(
            events_data, news_data, mtf_tech.get("_h1_candles") or [], intermarket=intermarket
        )

        # 4. Call AI Engine (Claude Sonnet/Haiku -> Gemini -> OpenRouter -> Quantitative 7-TF + Macro Engine)
        ai_res = await AIAgentEngine.synthesize_market_bias(
            symbol=symbol,
            price_snapshot=price_snapshot,
            technical_data=h1_tech,
            economic_events=events_data,
            news_articles=news_data,
            mtf_technical=mtf_tech,
            macro_context=macro_ctx,
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
