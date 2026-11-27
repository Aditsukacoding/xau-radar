"""
Signal History & Real OHLC Outcome Tracking Service (SL / TP1 / TP2 / TP3 Verifier).

Provides two transparent, verifiable streams in the TradeSignalHistory ledger:
1. LIVE Signals: Every trade setup generated in real time by AnalysisService, evaluated
   chronologically bar-by-bar against authentic live 15m/1h Yahoo Finance candles + spot price.
2. AUDIT_14D Verified Replay: On cold start / empty serverless DB, deterministically replays
   our exact Sniper Key-Zone detector (BOTH BUY & SELL setups) over the last 14 days of authentic
   Yahoo Finance 1H XAU/USD candles with ZERO lookahead and conservative SL-first tie-breaking.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.trade_signal_history import TradeSignalHistory
from app.providers import get_data_provider
from app.services.technical_calc import TechnicalCalculator
from app.services.macro_intelligence import MacroIntelligenceService
from app.services.post_mortem_service import PostMortemService
from app.schemas.signal_history import (
    SignalHistoryItem,
    SignalHistoryStats,
    SignalHistoryResponse,
)

logger = logging.getLogger(__name__)


def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _norm_candle_ts(raw: Any) -> Optional[datetime]:
    if isinstance(raw, datetime):
        return _to_utc(raw)
    if isinstance(raw, str):
        try:
            return _to_utc(datetime.fromisoformat(raw.replace("Z", "+00:00")))
        except Exception:
            return None
    return None


class SignalHistoryService:
    """Tracks, verifies, and summarizes real SL / TP1 / TP2 / TP3 outcomes for XAU/USD setups."""
    _last_eval_ts: Dict[str, float] = {}
    _legacy_purged_symbols: set = set()

    @staticmethod
    def _compute_realized_pips(
        outcome: str,
        risk_pips: float,
        r1: float,
        r2: float,
        r3: float,
        floating_pips: float = 0.0,
    ) -> float:
        """
        Matches our exact 3-tier Sniper lot-management profile:
        - 40% closed at TP1 (+60p) -> remaining 60% SL shifted to BEP
        - 40% closed at TP2        -> remaining 20% SL shifted to TP1
        - 20% runner closed at TP3
        """
        o = outcome.upper()
        if o == "SL_HIT":
            return round(-abs(risk_pips), 1)
        if o == "TP1_HIT":
            # 40% locked at TP1, remaining 60% stopped at BEP (0p)
            return round(0.40 * r1, 1)
        if o == "TP2_HIT":
            # 40% at TP1 + 40% at TP2 + 20% runner trailed out at TP1
            return round(0.40 * r1 + 0.40 * r2 + 0.20 * r1, 1)
        if o == "TP3_HIT":
            # Full 3-tier completion: 40% TP1 + 40% TP2 + 20% TP3
            return round(0.40 * r1 + 0.40 * r2 + 0.20 * r3, 1)
        if o == "ACTIVE":
            return round(floating_pips, 1)
        return 0.0

    @classmethod
    def _walk_candles_for_outcome(
        cls,
        action: str,
        execution_type: str,
        entry_price: float,
        stop_loss: float,
        tp1: float,
        tp2: float,
        tp3: float,
        risk_pips: float,
        r1: float,
        r2: float,
        r3: float,
        created_at: datetime,
        candles: List[Dict[str, Any]],
        curr_price: Optional[float] = None,
        now_utc: Optional[datetime] = None,
        expire_hours: float = 12.0,
    ) -> Dict[str, Any]:
        """
        Chronologically simulates/verifies exact entry fill and SL / TP1 / TP2 / TP3 hit
        across authentic OHLC bars. Conservative rule: if a bar touches BOTH SL and TP
        before TP1 is reached, SL_HIT takes precedence (zero optimistic cheating).
        """
        created_utc = _to_utc(created_at) or datetime.now(timezone.utc)
        ref_now = _to_utc(now_utc) or datetime.now(timezone.utc)
        is_buy = action.upper() == "BUY"
        is_instant = execution_type.upper() == "INSTANT"

        # Sort & filter candles strictly AFTER signal creation
        future_bars: List[Tuple[datetime, float, float, float, float]] = []
        for c in candles:
            ts = _norm_candle_ts(c.get("timestamp"))
            if ts is None or ts < created_utc:
                continue
            future_bars.append((
                ts,
                float(c["open"]),
                float(c["high"]),
                float(c["low"]),
                float(c["close"]),
            ))
        future_bars.sort(key=lambda x: x[0])

        triggered = is_instant
        triggered_at: Optional[datetime] = created_utc if is_instant else None
        tp1_hit = False
        tp2_hit = False
        tp1_ts: Optional[datetime] = None
        tp2_ts: Optional[datetime] = None
        mfe_pips = 0.0
        mae_pips = 0.0
        outcome = "ACTIVE" if is_instant else "PENDING_LIMIT"
        is_closed = False
        closed_at: Optional[datetime] = None
        hit_price: Optional[float] = None
        last_close = curr_price if (curr_price and curr_price > 0) else entry_price

        for ts, o, h, l, cl in future_bars:
            last_close = cl
            hours_since_create = (ts - created_utc).total_seconds() / 3600.0

            # Step 1: Check Limit Order Fill
            if not triggered:
                if hours_since_create > expire_hours:
                    outcome = "EXPIRED"
                    is_closed = True
                    closed_at = ts
                    hit_price = cl
                    break

                # Zone fill tolerance ($1.20 inside the key-zone pocket)
                filled = (l <= entry_price + 1.20) if is_buy else (h >= entry_price - 1.20)
                if not filled:
                    continue

                triggered = True
                triggered_at = ts
                outcome = "ACTIVE"

                # Conservative same-bar SL check on fill bar
                if (is_buy and l <= stop_loss) or ((not is_buy) and h >= stop_loss):
                    mae_pips = max(mae_pips, round(abs(entry_price - stop_loss) * 10.0, 1))
                    outcome = "SL_HIT"
                    is_closed = True
                    closed_at = ts
                    hit_price = stop_loss
                    break
                continue

            # Step 2: Track MFE & MAE once filled
            if is_buy:
                fav = max(0.0, (h - entry_price) * 10.0)
                adv = max(0.0, (entry_price - l) * 10.0)
            else:
                fav = max(0.0, (entry_price - l) * 10.0)
                adv = max(0.0, (h - entry_price) * 10.0)
            mfe_pips = max(mfe_pips, round(fav, 1))
            mae_pips = max(mae_pips, round(adv, 1))

            # Step 3: Progressive 3-tier TP & Trailing SL Evaluation
            if not tp1_hit:
                sl_touched = (l <= stop_loss) if is_buy else (h >= stop_loss)
                tp1_touched = (h >= tp1) if is_buy else (l <= tp1)

                # Conservative SL-first tie-breaker
                if sl_touched:
                    outcome = "SL_HIT"
                    is_closed = True
                    closed_at = ts
                    hit_price = stop_loss
                    break
                if tp1_touched:
                    tp1_hit = True
                    tp1_ts = ts
                    outcome = "TP1_HIT"
                    hit_price = tp1
                    # Check if same momentum bar also cleared TP2/TP3
                    if (is_buy and h >= tp2) or ((not is_buy) and l <= tp2):
                        tp2_hit = True
                        tp2_ts = ts
                        outcome = "TP2_HIT"
                        hit_price = tp2
                    if (is_buy and h >= tp3) or ((not is_buy) and l <= tp3):
                        outcome = "TP3_HIT"
                        is_closed = True
                        closed_at = ts
                        hit_price = tp3
                        break
            elif not tp2_hit:
                # SL has shifted to BEP (entry_price) after TP1!
                bep_touched = (l <= entry_price) if is_buy else (h >= entry_price)
                tp2_touched = (h >= tp2) if is_buy else (l <= tp2)

                if bep_touched and not tp2_touched:
                    outcome = "TP1_HIT"
                    is_closed = True
                    closed_at = ts
                    hit_price = entry_price
                    break
                if tp2_touched:
                    tp2_hit = True
                    tp2_ts = ts
                    outcome = "TP2_HIT"
                    hit_price = tp2
                    if (is_buy and h >= tp3) or ((not is_buy) and l <= tp3):
                        outcome = "TP3_HIT"
                        is_closed = True
                        closed_at = ts
                        hit_price = tp3
                        break
                elif bep_touched:
                    outcome = "TP1_HIT"
                    is_closed = True
                    closed_at = ts
                    hit_price = entry_price
                    break
            else:
                # TP2 already hit -> remaining 20% runner SL shifted to TP1
                tp1_trail_touched = (l <= tp1) if is_buy else (h >= tp1)
                tp3_touched = (h >= tp3) if is_buy else (l <= tp3)

                if tp3_touched and not tp1_trail_touched:
                    outcome = "TP3_HIT"
                    is_closed = True
                    closed_at = ts
                    hit_price = tp3
                    break
                if tp1_trail_touched:
                    outcome = "TP2_HIT"
                    is_closed = True
                    closed_at = ts
                    hit_price = tp1
                    break
                if tp3_touched:
                    outcome = "TP3_HIT"
                    is_closed = True
                    closed_at = ts
                    hit_price = tp3
                    break

        # Step 4: Live spot price check for currently open signals
        if not is_closed and curr_price and curr_price > 0:
            last_close = curr_price
            age_h = (ref_now - created_utc).total_seconds() / 3600.0
            if not triggered:
                if age_h > expire_hours:
                    outcome = "EXPIRED"
                    is_closed = True
                    closed_at = ref_now
                    hit_price = curr_price
                else:
                    filled_now = (curr_price <= entry_price + 1.20) if is_buy else (curr_price >= entry_price - 1.20)
                    if filled_now:
                        triggered = True
                        triggered_at = ref_now
                        outcome = "ACTIVE"
            if triggered and not is_closed:
                if is_buy:
                    mfe_pips = max(mfe_pips, round(max(0.0, (curr_price - entry_price) * 10.0), 1))
                    mae_pips = max(mae_pips, round(max(0.0, (entry_price - curr_price) * 10.0), 1))
                    if not tp1_hit and curr_price <= stop_loss:
                        outcome, is_closed, closed_at, hit_price = "SL_HIT", True, ref_now, stop_loss
                    elif curr_price >= tp3:
                        outcome, is_closed, closed_at, hit_price = "TP3_HIT", True, ref_now, tp3
                    elif curr_price >= tp2:
                        tp1_hit = tp2_hit = True
                        outcome, hit_price = "TP2_HIT", tp2
                    elif curr_price >= tp1:
                        tp1_hit = True
                        outcome, hit_price = "TP1_HIT", tp1
                else:
                    mfe_pips = max(mfe_pips, round(max(0.0, (entry_price - curr_price) * 10.0), 1))
                    mae_pips = max(mae_pips, round(max(0.0, (curr_price - entry_price) * 10.0), 1))
                    if not tp1_hit and curr_price >= stop_loss:
                        outcome, is_closed, closed_at, hit_price = "SL_HIT", True, ref_now, stop_loss
                    elif curr_price <= tp3:
                        outcome, is_closed, closed_at, hit_price = "TP3_HIT", True, ref_now, tp3
                    elif curr_price <= tp2:
                        tp1_hit = tp2_hit = True
                        outcome, hit_price = "TP2_HIT", tp2
                    elif curr_price <= tp1:
                        tp1_hit = True
                        outcome, hit_price = "TP1_HIT", tp1

        floating_pips = 0.0
        if triggered and not is_closed and last_close > 0:
            floating_pips = round(((last_close - entry_price) if is_buy else (entry_price - last_close)) * 10.0, 1)

        realized = cls._compute_realized_pips(outcome, risk_pips, r1, r2, r3, floating_pips=floating_pips)

        # Build clear Indonesian WIB note explaining exact execution history
        trig_wib = MacroIntelligenceService.format_wib_id(triggered_at) if triggered_at else None
        close_wib = MacroIntelligenceService.format_wib_id(closed_at) if closed_at else None

        if outcome == "TP3_HIT":
            note = (
                f"Terjemput {trig_wib} → Full Target TP3 (${tp3:.2f}) tercapai pada {close_wib}. "
                f"Realisasi 3-tier: +{realized:.0f} pips (puncak +{mfe_pips:.0f}p)."
            )
        elif outcome == "TP2_HIT":
            if is_closed:
                note = (
                    f"Terjemput {trig_wib} → TP1 (+{r1:.0f}p) & TP2 (+{r2:.0f}p) tercapai, sisa 20% ditutup trailing di TP1 "
                    f"pada {close_wib}. Net profit: +{realized:.0f} pips."
                )
            else:
                note = (
                    f"Terjemput {trig_wib} → TP2 (${tp2:.2f}) sudah tercapai! 80% lot aman, sisa 20% runner menuju TP3 (${tp3:.2f})."
                )
        elif outcome == "TP1_HIT":
            if is_closed:
                note = (
                    f"Terjemput {trig_wib} → TP1 (+{r1:.0f}p) diamankan (40% lot), sisa 60% terkena BEP di ${entry_price:.2f} "
                    f"pada {close_wib}. Net profit: +{realized:.0f} pips."
                )
            else:
                note = (
                    f"Terjemput {trig_wib} → TP1 (${tp1:.2f}, +{r1:.0f}p) sudah tercapai! SL geser ke BEP, lanjut ke TP2 (${tp2:.2f})."
                )
        elif outcome == "SL_HIT":
            note = (
                f"Terjemput {trig_wib} → Harga menyentuh Stop Loss (${stop_loss:.2f}) pada {close_wib} "
                f"(-{risk_pips:.0f} pips). Sempat floating +{mfe_pips:.0f}p sebelum berbalik."
            )
        elif outcome == "EXPIRED":
            note = f"Zona limit tidak tersentuh harga dalam {int(expire_hours)} jam — setup dibatalkan (tidak terisi, 0 pips)."
        elif outcome == "ACTIVE":
            sign = "+" if floating_pips >= 0 else ""
            note = f"Terjemput {trig_wib} → Posisi {action} sedang berjalan (floating {sign}{floating_pips:.1f} pips, puncak +{mfe_pips:.0f}p)."
        else:
            note = f"Menunggu harga menjemput Key Zone {action} di sekitar ${entry_price:.2f}."

        return {
            "outcome": outcome,
            "is_closed": is_closed,
            "triggered_at": triggered_at,
            "closed_at": closed_at,
            "hit_price": hit_price,
            "max_favorable_pips": mfe_pips,
            "max_adverse_pips": mae_pips,
            "realized_pips": realized,
            "outcome_note": note,
        }

    @classmethod
    def record_live_signal(
        cls,
        db: Session,
        symbol: str,
        trade_setup: Dict[str, Any],
        created_at: Optional[datetime] = None,
    ) -> Optional[TradeSignalHistory]:
        """Records a live BUY or SELL trade setup in the signal history ledger (deduplicated)."""
        if not isinstance(trade_setup, dict):
            return None
        action = str(trade_setup.get("action", "WAIT")).upper()
        if action not in ("BUY", "SELL"):
            return None

        entry_p = float(trade_setup.get("entry_price") or 0.0)
        sl = float(trade_setup.get("stop_loss") or 0.0)
        tp1 = float(trade_setup.get("take_profit_1") or 0.0)
        tp2 = float(trade_setup.get("take_profit_2") or 0.0)
        tp3 = float(trade_setup.get("take_profit_3") or 0.0)
        if entry_p <= 0 or sl <= 0 or tp1 <= 0:
            return None

        now_utc = _to_utc(created_at) or datetime.now(timezone.utc)
        sym = symbol.upper()

        # Layer 1 Bulletproof Anti-Duplicate Guard (checks BOTH open AND already-closed LIVE rows!)
        # Prevents re-inserting an already-closed AnalysisReport when Riwayat is reloaded before Dashboard refreshes.
        recent_rows = (
            db.query(TradeSignalHistory)
            .filter(
                TradeSignalHistory.symbol == sym,
                TradeSignalHistory.source_type == "LIVE",
            )
            .order_by(desc(TradeSignalHistory.created_at))
            .limit(20)
            .all()
        )
        for existing in recent_rows:
            same_prices = (
                existing.action == action
                and abs(existing.entry_price - entry_p) <= 0.60
                and abs(existing.stop_loss - sl) <= 0.60
            )
            if not same_prices:
                continue
            ex_utc = _to_utc(existing.created_at)
            if ex_utc is not None:
                dt_sec = abs((now_utc - ex_utc).total_seconds())
                # Exact same AnalysisReport timestamp (within 3 min) OR already closed same setup within 24h -> NEVER clone!
                if dt_sec <= 180.0 or (existing.is_closed and dt_sec <= 86400.0):
                    return existing

        # Strict single-active-signal rule synced 1-to-1 with Dashboard's locked setup
        existing_open = next((r for r in recent_rows if not r.is_closed), None)
        if existing_open:
            same_setup = (
                existing_open.action == action
                and abs(existing_open.entry_price - entry_p) <= 1.00
                and abs(existing_open.stop_loss - sl) <= 1.00
            )
            if same_setup:
                return existing_open
            # If the old open row was already triggered (ACTIVE/TP1/TP2), never overwrite it!
            if existing_open.outcome != "PENDING_LIMIT" or existing_open.triggered_at is not None:
                return existing_open
            # Otherwise it was an unfilled superseded PENDING_LIMIT — replace it cleanly so Ledger matches Dashboard 1-to-1
            db.delete(existing_open)
            db.commit()

        exec_type = str(trade_setup.get("execution_type", "LIMIT")).upper()
        init_outcome = "ACTIVE" if exec_type == "INSTANT" else "PENDING_LIMIT"
        trig_at = now_utc if exec_type == "INSTANT" else None

        risk_p = float(trade_setup.get("risk_pips") or round(abs(entry_p - sl) * 10.0, 1))
        r1 = float(trade_setup.get("reward_tp1_pips") or round(abs(tp1 - entry_p) * 10.0, 1))
        r2 = float(trade_setup.get("reward_tp2_pips") or round(abs(tp2 - entry_p) * 10.0, 1))
        r3 = float(trade_setup.get("reward_tp3_pips") or round(abs(tp3 - entry_p) * 10.0, 1))

        row = TradeSignalHistory(
            symbol=symbol.upper(),
            source_type="LIVE",
            action=action,
            action_label=str(trade_setup.get("action_label") or f"{action} LIMIT (KEY ZONE)"),
            execution_type=exec_type,
            entry_zone=str(trade_setup.get("entry_zone") or f"${entry_p - 0.8:.2f} - ${entry_p + 0.8:.2f}"),
            entry_price=round(entry_p, 2),
            stop_loss=round(sl, 2),
            take_profit_1=round(tp1, 2),
            take_profit_2=round(tp2, 2),
            take_profit_3=round(tp3, 2),
            risk_pips=round(risk_p, 1),
            reward_tp1_pips=round(r1, 1),
            reward_tp2_pips=round(r2, 1),
            reward_tp3_pips=round(r3, 1),
            setup_quality_score=int(trade_setup.get("setup_quality_score") or 78),
            mtf_alignment=str(trade_setup.get("mtf_alignment") or ""),
            zone_proof=str(trade_setup.get("zone_proof") or ""),
            session_name=str(trade_setup.get("session_name") or ""),
            outcome=init_outcome,
            is_closed=False,
            triggered_at=trig_at,
            outcome_note=str(trade_setup.get("status_message") or f"Sinyal {action} aktif di ${entry_p:.2f}."),
            created_at=now_utc,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @classmethod
    def _cleanup_duplicate_open_signals(cls, db: Session, symbol: str) -> int:
        """
        Cleans BOTH:
          1. Duplicate accidental clones (same action, entry_price, stop_loss & created_at within 3 min),
             keeping only the earliest original row (lowest id).
          2. Multiple concurrent unclosed LIVE rows (keeps only the single row matching locked AnalysisReport).
        """
        sym = symbol.upper()
        all_live = (
            db.query(TradeSignalHistory)
            .filter(
                TradeSignalHistory.symbol == sym,
                TradeSignalHistory.source_type == "LIVE",
            )
            .order_by(TradeSignalHistory.id.asc())
            .all()
        )
        removed = 0
        kept_fingerprints: List[Tuple[str, float, float, Optional[datetime]]] = []
        surviving_open: List[TradeSignalHistory] = []

        for row in all_live:
            r_utc = _to_utc(row.created_at)
            is_clone = False
            for fp_act, fp_entry, fp_sl, fp_ts in kept_fingerprints:
                if (
                    row.action == fp_act
                    and abs(row.entry_price - fp_entry) <= 0.60
                    and abs(row.stop_loss - fp_sl) <= 0.60
                    and r_utc is not None
                    and fp_ts is not None
                    and abs((r_utc - fp_ts).total_seconds()) <= 180.0
                ):
                    is_clone = True
                    break
            if is_clone:
                db.delete(row)
                removed += 1
            else:
                kept_fingerprints.append((row.action, row.entry_price, row.stop_loss, r_utc))
                if not row.is_closed:
                    surviving_open.append(row)

        if len(surviving_open) > 1:
            surviving_open.sort(
                key=lambda x: (_to_utc(x.created_at) or datetime.min.replace(tzinfo=timezone.utc)).timestamp(),
                reverse=True,
            )
            keep_id = surviving_open[0].id
            try:
                import json
                from app.models.analysis_report import AnalysisReport
                latest_rep = (
                    db.query(AnalysisReport)
                    .filter(AnalysisReport.symbol == sym)
                    .order_by(desc(AnalysisReport.created_at))
                    .first()
                )
                if latest_rep and latest_rep.trade_setup_json:
                    active_ts = json.loads(latest_rep.trade_setup_json)
                    act_entry = float(active_ts.get("entry_price") or 0.0)
                    act_sl = float(active_ts.get("stop_loss") or 0.0)
                    for row in surviving_open:
                        if abs(row.entry_price - act_entry) <= 0.50 and abs(row.stop_loss - act_sl) <= 0.50:
                            keep_id = row.id
                            break
            except Exception:
                pass
            for row in surviving_open:
                if row.id != keep_id:
                    db.delete(row)
                    removed += 1

        if removed:
            db.commit()
        return removed

    @classmethod
    def reset_history(cls, db: Session, symbol: str = "XAUUSD") -> int:
        """
        Cleanly clears the LIVE signal ledger AND invalidates stale AnalysisReports for `symbol`
        so tracking restarts fresh from 0W/0L without ghost re-imports of old closed reports.
        """
        from app.models.analysis_report import AnalysisReport
        sym = symbol.upper()
        deleted_sigs = (
            db.query(TradeSignalHistory)
            .filter(TradeSignalHistory.symbol == sym)
            .delete(synchronize_session=False)
        )
        db.query(AnalysisReport).filter(AnalysisReport.symbol == sym).delete(synchronize_session=False)
        db.commit()
        cls._last_eval_ts.pop(sym, None)
        return int(deleted_sigs or 0)

    @classmethod
    async def evaluate_open_signals(
        cls,
        db: Session,
        symbol: str = "XAUUSD",
        curr_price: Optional[float] = None,
        force: bool = False,
    ) -> int:
        """Evaluates unclosed signals against authentic live 15m Yahoo Finance candles + live spot (with 45s cache)."""
        import time
        sym = symbol.upper()
        now_ts = time.time()
        if not force and (now_ts - cls._last_eval_ts.get(sym, 0.0)) < 45.0:
            return 0

        cls._cleanup_duplicate_open_signals(db, sym)

        open_rows = (
            db.query(TradeSignalHistory)
            .filter(
                TradeSignalHistory.symbol == sym,
                TradeSignalHistory.source_type == "LIVE",
                TradeSignalHistory.is_closed == False,
            )
            .order_by(TradeSignalHistory.created_at.asc())
            .all()
        )
        if not open_rows:
            cls._last_eval_ts[sym] = now_ts
            return 0

        provider = get_data_provider()
        if not curr_price or curr_price <= 0:
            try:
                snap = await provider.get_latest_price(sym)
                curr_price = float(snap.get("current_price") or 0.0)
            except Exception:
                curr_price = 0.0

        try:
            candles = await provider.get_price_candles(symbol=sym, timeframe="15m", count=180)
        except Exception:
            candles = []

        import json
        updated = 0
        dirty = False
        now_utc = datetime.now(timezone.utc)
        last_closed = (
            db.query(TradeSignalHistory)
            .filter(
                TradeSignalHistory.symbol == sym,
                TradeSignalHistory.source_type == "LIVE",
                TradeSignalHistory.is_closed == True,
            )
            .order_by(desc(TradeSignalHistory.closed_at))
            .first()
        )
        for sig in open_rows:
            res = cls._walk_candles_for_outcome(
                action=sig.action,
                execution_type=sig.execution_type,
                entry_price=sig.entry_price,
                stop_loss=sig.stop_loss,
                tp1=sig.take_profit_1,
                tp2=sig.take_profit_2,
                tp3=sig.take_profit_3,
                risk_pips=sig.risk_pips,
                r1=sig.reward_tp1_pips,
                r2=sig.reward_tp2_pips,
                r3=sig.reward_tp3_pips,
                created_at=sig.created_at,
                candles=candles,
                curr_price=curr_price,
                now_utc=now_utc,
                expire_hours=12.0,
            )
            prev_state = (
                sig.outcome,
                bool(sig.is_closed),
                _to_utc(sig.triggered_at),
                _to_utc(sig.closed_at),
                sig.hit_price,
                round(sig.max_favorable_pips or 0.0, 2),
                round(sig.max_adverse_pips or 0.0, 2),
                round(sig.realized_pips or 0.0, 2),
                sig.outcome_note or "",
            )
            next_state = (
                res["outcome"],
                bool(res["is_closed"]),
                _to_utc(res["triggered_at"]),
                _to_utc(res["closed_at"]),
                res["hit_price"],
                round(res["max_favorable_pips"] or 0.0, 2),
                round(res["max_adverse_pips"] or 0.0, 2),
                round(res["realized_pips"] or 0.0, 2),
                res["outcome_note"] or "",
            )
            if prev_state != next_state or res["is_closed"]:
                sig.outcome = res["outcome"]
                sig.is_closed = res["is_closed"]
                sig.triggered_at = res["triggered_at"]
                sig.closed_at = res["closed_at"]
                sig.hit_price = res["hit_price"]
                sig.max_favorable_pips = res["max_favorable_pips"]
                sig.max_adverse_pips = res["max_adverse_pips"]
                sig.realized_pips = res["realized_pips"]
                sig.outcome_note = res["outcome_note"]
                if prev_state != next_state:
                    dirty = True
                if sig.is_closed:
                    pm = PostMortemService.evaluate_closed_trade(sig, candles, prev_closed_trade=last_closed)
                    sig.post_mortem_json = json.dumps(pm, ensure_ascii=False)
                    last_closed = sig
                    dirty = True
                updated += 1

        if dirty:
            db.commit()
        cls._last_eval_ts[sym] = now_ts
        return updated

    @classmethod
    async def ensure_verified_history(cls, db: Session, symbol: str = "XAUUSD") -> int:
        """
        Ensures the Signal History ledger is populated with authentic, zero-lookahead 14-day
        verified structural setups (BOTH BUY & SELL) evaluated against real Yahoo Finance 1H
        XAU/USD OHLC candles. Essential for serverless cold starts where /tmp SQLite resets.
        """
        sym = symbol.upper()
        existing_audit = (
            db.query(TradeSignalHistory)
            .filter(TradeSignalHistory.symbol == sym, TradeSignalHistory.source_type == "AUDIT_14D")
            .count()
        )
        if existing_audit >= 8:
            return 0

        provider = get_data_provider()
        try:
            h1_candles = await provider.get_price_candles(symbol=sym, timeframe="1h", count=260)
        except Exception as e:
            logger.warning(f"[SignalHistory] Failed to fetch 1H candles for 14-day audit: {e}")
            return 0

        if not h1_candles or len(h1_candles) < 60:
            return 0

        # Ensure chronological sort
        bars = sorted(
            [c for c in h1_candles if _norm_candle_ts(c.get("timestamp")) is not None],
            key=lambda c: _norm_candle_ts(c["timestamp"]),
        )
        if len(bars) < 60:
            return 0

        created_rows: List[TradeSignalHistory] = []
        # Walk forward through authentic past 1H bars every 6 hours (leaving at least 3 bars to evaluate)
        step = 6
        start_idx = 42
        end_idx = len(bars) - 3

        for i in range(start_idx, end_idx, step):
            window = bars[max(0, i - 60): i + 1]
            future = bars[i + 1: min(len(bars), i + 30)]
            if len(window) < 25 or len(future) < 4:
                continue

            bar_ts = _norm_candle_ts(window[-1]["timestamp"])
            if bar_ts is None:
                continue
            spot = round(float(window[-1]["close"]), 2)

            ind = TechnicalCalculator.calculate_indicators(window)
            trend = str(ind.get("trend_direction", "SIDEWAYS")).upper()
            rsi = ind.get("rsi_14")
            atr = float(ind.get("atr_14") or 4.5)
            pa = str(ind.get("price_action", "")).upper()
            demands = ind.get("structural_demand_zones") or []
            supplies = ind.get("structural_supply_zones") or []
            sups = [float(x) for x in (ind.get("support_levels") or []) if float(x) < spot]
            ress = [float(x) for x in (ind.get("resistance_levels") or []) if float(x) > spot]
            sess = TechnicalCalculator.detect_active_session(bar_ts)

            # Determine authentic balanced BUY vs SELL directional trigger (strictly using past bars only!)
            action: Optional[str] = None
            reason_tag = ""
            if trend == "BULLISH" and (not isinstance(rsi, (int, float)) or rsi < 70):
                action = "BUY"
                reason_tag = "H1 BULLISH • Demand Retest"
            elif trend == "BEARISH" and (not isinstance(rsi, (int, float)) or rsi > 30):
                action = "SELL"
                reason_tag = "H1 BEARISH • Supply Retest"
            elif isinstance(rsi, (int, float)) and rsi <= 33 and pa.startswith("BULLISH"):
                action = "BUY"
                reason_tag = f"Oversold Reversal (RSI {rsi:.0f})"
            elif isinstance(rsi, (int, float)) and rsi >= 67 and pa.startswith("BEARISH"):
                action = "SELL"
                reason_tag = f"Overbought Reversal (RSI {rsi:.0f})"
            else:
                # In sideways / consolidation, trade the nearer proven structural wall (BUY Demand or SELL Supply)
                d_dist = abs(spot - float(demands[0]["price"])) if demands else 999.0
                s_dist = abs(float(supplies[0]["price"]) - spot) if supplies else 999.0
                if d_dist < s_dist and d_dist <= 18.0:
                    action = "BUY"
                    reason_tag = "Range Demand Bounce"
                elif s_dist <= 18.0:
                    action = "SELL"
                    reason_tag = "Range Supply Rejection"

            if action is None:
                continue

            # Strict Sniper profile: SL 35–48p, TP1 +60p, TP2 structural (+105–155p), TP3 structural (+165–220p)
            risk = round(max(3.50, min(4.80, 3.20 + atr * 0.12)), 2)

            if action == "BUY":
                safe_d = [z for z in demands if 2.0 <= (spot - float(z["price"])) <= 18.0]
                if safe_d:
                    entry_p = round(float(safe_d[0]["price"]), 2)
                    q_score = int(min(92, max(74, 72 + int(safe_d[0].get("rejections", 1)) * 5)))
                    proof = f"Diuji {safe_d[0].get('touches', 2)}× ({safe_d[0].get('rejections', 1)}× reject) • Demand H1"
                elif sups and 2.0 <= (spot - sups[0]) <= 18.0:
                    entry_p = round(sups[0], 2)
                    q_score = 76
                    proof = "Support Struktural H1"
                else:
                    entry_p = round(spot - max(2.50, min(6.50, atr * 0.45)), 2)
                    q_score = 74
                    proof = "Area Pullback Demand H1"

                e_low, e_high = round(entry_p - 0.70, 2), round(entry_p + 0.70, 2)
                sl = round(entry_p - risk, 2)
                tp1 = round(entry_p + 6.00, 2)
                tp2_cand = next((round(r - 0.50, 2) for r in sorted(ress) if (entry_p + 9.50) <= r <= (entry_p + 18.0)), None)
                tp2 = tp2_cand if tp2_cand else round(entry_p + 11.50, 2)
                tp3 = round(max(tp2 + 5.50, entry_p + 17.50), 2)
                label = "BUY LIMIT (KEY DEMAND)"
            else:
                safe_s = [z for z in supplies if 2.0 <= (float(z["price"]) - spot) <= 18.0]
                if safe_s:
                    entry_p = round(float(safe_s[0]["price"]), 2)
                    q_score = int(min(92, max(74, 72 + int(safe_s[0].get("rejections", 1)) * 5)))
                    proof = f"Diuji {safe_s[0].get('touches', 2)}× ({safe_s[0].get('rejections', 1)}× reject) • Supply H1"
                elif ress and 2.0 <= (ress[0] - spot) <= 18.0:
                    entry_p = round(ress[0], 2)
                    q_score = 76
                    proof = "Resistance Struktural H1"
                else:
                    entry_p = round(spot + max(2.50, min(6.50, atr * 0.45)), 2)
                    q_score = 74
                    proof = "Area Pullback Supply H1"

                e_low, e_high = round(entry_p - 0.70, 2), round(entry_p + 0.70, 2)
                sl = round(entry_p + risk, 2)
                tp1 = round(entry_p - 6.00, 2)
                tp2_cand = next((round(s + 0.50, 2) for s in sorted(sups, reverse=True) if (entry_p - 18.0) <= s <= (entry_p - 9.50)), None)
                tp2 = tp2_cand if tp2_cand else round(entry_p - 11.50, 2)
                tp3 = round(min(tp2 - 5.50, entry_p - 17.50), 2)
                label = "SELL LIMIT (KEY SUPPLY)"

            risk_p = round(abs(entry_p - sl) * 10.0, 1)
            r1 = round(abs(tp1 - entry_p) * 10.0, 1)
            r2 = round(abs(tp2 - entry_p) * 10.0, 1)
            r3 = round(abs(tp3 - entry_p) * 10.0, 1)

            eval_res = cls._walk_candles_for_outcome(
                action=action,
                execution_type="LIMIT",
                entry_price=entry_p,
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                tp3=tp3,
                risk_pips=risk_p,
                r1=r1,
                r2=r2,
                r3=r3,
                created_at=bar_ts,
                candles=future,
                curr_price=None,
                now_utc=_norm_candle_ts(future[-1]["timestamp"]) or datetime.now(timezone.utc),
                expire_hours=12.0,
            )

            # Keep finalized filled trades (TP1/TP2/TP3/SL) plus occasional expired limit for transparency
            if not eval_res["is_closed"]:
                continue

            created_rows.append(
                TradeSignalHistory(
                    symbol=sym,
                    source_type="AUDIT_14D",
                    action=action,
                    action_label=label,
                    execution_type="LIMIT",
                    entry_zone=f"${e_low:.2f} - ${e_high:.2f}",
                    entry_price=entry_p,
                    stop_loss=sl,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    take_profit_3=tp3,
                    risk_pips=risk_p,
                    reward_tp1_pips=r1,
                    reward_tp2_pips=r2,
                    reward_tp3_pips=r3,
                    setup_quality_score=q_score,
                    mtf_alignment=reason_tag,
                    zone_proof=proof,
                    session_name=sess["name"],
                    outcome=eval_res["outcome"],
                    is_closed=True,
                    triggered_at=eval_res["triggered_at"],
                    closed_at=eval_res["closed_at"],
                    hit_price=eval_res["hit_price"],
                    max_favorable_pips=eval_res["max_favorable_pips"],
                    max_adverse_pips=eval_res["max_adverse_pips"],
                    realized_pips=eval_res["realized_pips"],
                    outcome_note=eval_res["outcome_note"],
                    created_at=bar_ts,
                )
            )

        # Store latest 24 authentic verified setups
        selected = created_rows[-24:]
        if selected:
            db.add_all(selected)
            db.commit()
        return len(selected)

    @classmethod
    async def get_history_response(
        cls,
        db: Session,
        symbol: str = "XAUUSD",
        action_filter: str = "ALL",
        outcome_filter: str = "ALL",
        limit: int = 40,
        force_eval: bool = False,
    ) -> SignalHistoryResponse:
        sym = symbol.upper()
        provider = get_data_provider()
        try:
            snap = await provider.get_latest_price(sym)
            curr_price = float(snap.get("current_price") or 0.0)
        except Exception:
            curr_price = 0.0

        # 1. Pure LIVE-only ledger: purge any legacy non-LIVE rows once per worker process
        if sym not in cls._legacy_purged_symbols:
            legacy_audit = (
                db.query(TradeSignalHistory)
                .filter(TradeSignalHistory.symbol == sym, TradeSignalHistory.source_type != "LIVE")
                .delete(synchronize_session=False)
            )
            if legacy_audit:
                db.commit()
            cls._legacy_purged_symbols.add(sym)

        # 1b. Keep LIVE ledger synced 1-to-1 with the current locked Dashboard setup
        try:
            import json
            from app.models.analysis_report import AnalysisReport
            latest_rep = (
                db.query(AnalysisReport)
                .filter(AnalysisReport.symbol == sym)
                .order_by(desc(AnalysisReport.created_at))
                .first()
            )
            if latest_rep and latest_rep.trade_setup_json:
                cls.record_live_signal(db, sym, json.loads(latest_rep.trade_setup_json), latest_rep.created_at)
        except Exception:
            pass

        # 2. Re-evaluate open LIVE signal against latest 15m candles + spot price (45s cache unless force_eval)
        await cls.evaluate_open_signals(db, sym, curr_price=curr_price, force=force_eval)

        # 3. Query ONLY real-time LIVE records (zero backtest/demo data)
        all_rows = (
            db.query(TradeSignalHistory)
            .filter(TradeSignalHistory.symbol == sym, TradeSignalHistory.source_type == "LIVE")
            .order_by(desc(TradeSignalHistory.created_at))
            .limit(80)
            .all()
        )

        # 3b. Automatically generate forensic Post-Mortem for any closed trade missing post_mortem_json!
        missing_pm = [r for r in all_rows if r.is_closed and not getattr(r, "post_mortem_json", None)]
        if missing_pm:
            import json
            try:
                m15_hist = await provider.get_price_candles(symbol=sym, timeframe="15m", count=250)
            except Exception:
                m15_hist = []
            # Walk oldest-to-newest so prev_closed_trade detects back-to-back revenge SL accurately
            closed_chrono = sorted(
                [r for r in all_rows if r.is_closed],
                key=lambda x: (_to_utc(x.closed_at or x.created_at) or datetime.min.replace(tzinfo=timezone.utc)).timestamp(),
            )
            prev_tr = None
            pm_dirty = False
            for row in closed_chrono:
                if not getattr(row, "post_mortem_json", None):
                    pm_dict = PostMortemService.evaluate_closed_trade(row, m15_hist, prev_closed_trade=prev_tr)
                    row.post_mortem_json = json.dumps(pm_dict, ensure_ascii=False)
                    pm_dirty = True
                prev_tr = row
            if pm_dirty:
                try:
                    db.commit()
                except Exception:
                    db.rollback()

        # Compute transparent stats across all records (before UI filters)
        wins = 0
        losses = 0
        expired = 0
        active_or_pending = 0
        tp1_hits = 0
        tp2_hits = 0
        tp3_hits = 0
        sl_hits = 0
        buy_count = 0
        sell_count = 0
        buy_wins = 0
        sell_wins = 0
        gross_win_pips = 0.0
        gross_loss_pips = 0.0

        for r in all_rows:
            if r.action == "BUY":
                buy_count += 1
            elif r.action == "SELL":
                sell_count += 1

            o = r.outcome.upper()
            if o == "TP1_HIT":
                tp1_hits += 1
                wins += 1
                gross_win_pips += max(0.0, r.realized_pips)
                if r.action == "BUY":
                    buy_wins += 1
                else:
                    sell_wins += 1
            elif o == "TP2_HIT":
                tp2_hits += 1
                wins += 1
                gross_win_pips += max(0.0, r.realized_pips)
                if r.action == "BUY":
                    buy_wins += 1
                else:
                    sell_wins += 1
            elif o == "TP3_HIT":
                tp3_hits += 1
                wins += 1
                gross_win_pips += max(0.0, r.realized_pips)
                if r.action == "BUY":
                    buy_wins += 1
                else:
                    sell_wins += 1
            elif o == "SL_HIT":
                sl_hits += 1
                losses += 1
                gross_loss_pips += abs(r.realized_pips)
            elif o == "EXPIRED":
                expired += 1
            else:
                active_or_pending += 1

        decided = wins + losses
        win_rate = round((wins / decided) * 100.0, 1) if decided > 0 else 0.0
        net_pips = round(gross_win_pips - gross_loss_pips, 1)
        avg_win = round(gross_win_pips / wins, 1) if wins > 0 else 0.0
        avg_loss = round(gross_loss_pips / losses, 1) if losses > 0 else 0.0
        pf = round(gross_win_pips / gross_loss_pips, 2) if gross_loss_pips > 0 else (round(gross_win_pips, 2) if gross_win_pips > 0 else 0.0)

        stats = SignalHistoryStats(
            total_signals=len(all_rows),
            closed_trades=decided,
            active_or_pending=active_or_pending,
            wins=wins,
            losses=losses,
            expired=expired,
            tp1_hits=tp1_hits,
            tp2_hits=tp2_hits,
            tp3_hits=tp3_hits,
            sl_hits=sl_hits,
            buy_count=buy_count,
            sell_count=sell_count,
            buy_wins=buy_wins,
            sell_wins=sell_wins,
            win_rate_pct=win_rate,
            net_pips=net_pips,
            avg_win_pips=avg_win,
            avg_loss_pips=avg_loss,
            profit_factor=pf,
        )

        # Apply user UI filters
        act_f = action_filter.upper()
        out_f = outcome_filter.upper()
        filtered: List[TradeSignalHistory] = []
        for r in all_rows:
            if act_f in ("BUY", "SELL") and r.action.upper() != act_f:
                continue
            o = r.outcome.upper()
            if out_f == "WIN" and o not in ("TP1_HIT", "TP2_HIT", "TP3_HIT"):
                continue
            if out_f == "LOSS" and o != "SL_HIT":
                continue
            if out_f == "OPEN" and o not in ("PENDING_LIMIT", "ACTIVE"):
                continue
            filtered.append(r)

        # Prioritize LIVE open signals at top, then chronological newest-first
        filtered.sort(
            key=lambda x: (
                1 if (x.source_type == "LIVE" and not x.is_closed) else 0,
                (_to_utc(x.created_at) or datetime.min.replace(tzinfo=timezone.utc)).timestamp(),
            ),
            reverse=True,
        )

        import json as _json
        items: List[SignalHistoryItem] = []
        for r in filtered[:limit]:
            pm_obj = None
            if getattr(r, "post_mortem_json", None):
                try:
                    pm_obj = _json.loads(r.post_mortem_json)
                except Exception:
                    pm_obj = None
            items.append(
                SignalHistoryItem(
                    id=r.id,
                    symbol=r.symbol,
                    source_type=r.source_type,
                    action=r.action,
                    action_label=r.action_label,
                    execution_type=r.execution_type,
                    entry_zone=r.entry_zone,
                    entry_price=r.entry_price,
                    stop_loss=r.stop_loss,
                    take_profit_1=r.take_profit_1,
                    take_profit_2=r.take_profit_2,
                    take_profit_3=r.take_profit_3,
                    risk_pips=r.risk_pips,
                    reward_tp1_pips=r.reward_tp1_pips,
                    reward_tp2_pips=r.reward_tp2_pips,
                    reward_tp3_pips=r.reward_tp3_pips,
                    setup_quality_score=r.setup_quality_score,
                    mtf_alignment=r.mtf_alignment or "",
                    zone_proof=r.zone_proof or "",
                    session_name=r.session_name or "",
                    outcome=r.outcome,
                    is_closed=r.is_closed,
                    triggered_at=r.triggered_at,
                    closed_at=r.closed_at,
                    hit_price=r.hit_price,
                    max_favorable_pips=r.max_favorable_pips,
                    max_adverse_pips=r.max_adverse_pips,
                    realized_pips=r.realized_pips,
                    outcome_note=r.outcome_note or "",
                    post_mortem=pm_obj,
                    created_at=r.created_at,
                    created_at_wib=MacroIntelligenceService.format_wib_id(r.created_at),
                    triggered_at_wib=MacroIntelligenceService.format_wib_id(r.triggered_at) if r.triggered_at else None,
                    closed_at_wib=MacroIntelligenceService.format_wib_id(r.closed_at) if r.closed_at else None,
                )
            )

        self_eval = PostMortemService.build_adaptive_learning_profile(db, sym)

        return SignalHistoryResponse(
            symbol=sym,
            current_price=round(curr_price, 2),
            updated_at_wib=MacroIntelligenceService.format_wib_id(datetime.now(timezone.utc), with_day=True, with_year=True),
            stats=stats,
            self_evaluation=self_eval,
            items=items,
            methodology_note=(
                "100% pencatatan LIVE real-time dari awal (tanpa backtest/simulasi). Setiap SL/TP dievaluasi otomatis "
                "secara mandiri (Post-Mortem M15) dan pelajarannya langsung diumpankan kembali ke AI & guardrail risiko."
            ),
        )
