"""
Autonomous Self-Evaluation & Adaptive Post-Mortem Engine.

Whenever a LIVE signal closes (especially SL_HIT, and also TP_HIT to reinforce what worked),
this engine inspects the real M15 OHLC candles around trigger & close to diagnose:
  1. BLIND_KNIFE_CATCH       — Filled directly inside a large opposing M15 impulse bar (>= 50p body).
  2. SWEEP_AND_REVERSE       — Liquidity stop-hunt swept SL, then price reversed strongly in our direction.
  3. MIXED_CHOP_ENTRY        — Opened while 7-TF alignment was MIXED/indecisive (e.g. 3B/3S).
  4. REVENGE_BACK_TO_BACK_SL — Opened another trade within 45 min of a previous SL_HIT.
  5. PREMATURE_REVERSAL      — Reached significant floating profit (MFE >= 40p) then reversed to SL before TP1.
  6. TREND_BREAKOUT_AGAINST  — Clean directional breakout invalidated the setup without reversing.

It then synthesizes an Adaptive Learning Profile that:
  - Feeds concrete, data-backed lessons directly into Gemini / OpenRouter AI prompts.
  - Dynamically adjusts Quantitative Guardrails (SL ATR buffer, Post-SL Cooldown, Anti-Mixed Chop Filter,
    deeper outer-edge Key Zone entry, and reachable TP1 calibration).
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.trade_signal_history import TradeSignalHistory

logger = logging.getLogger(__name__)


def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _norm_ts(raw: Any) -> Optional[datetime]:
    if isinstance(raw, datetime):
        return _to_utc(raw)
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(float(raw), tz=timezone.utc)
        except Exception:
            return None
    if isinstance(raw, str):
        try:
            return _to_utc(datetime.fromisoformat(raw.replace("Z", "+00:00")))
        except Exception:
            return None
    return None


class PostMortemService:
    """Forensic trade evaluator & self-adapting feedback engine for XAU/USD signals."""

    @classmethod
    def evaluate_closed_trade(
        cls,
        sig: TradeSignalHistory,
        m15_candles: List[Dict[str, Any]],
        prev_closed_trade: Optional[TradeSignalHistory] = None,
    ) -> Dict[str, Any]:
        """
        Performs objective candle-verified forensic diagnosis on a single closed trade.
        Returns structured JSON-serializable post-mortem dict.
        """
        outcome = str(sig.outcome or "").upper()
        action = str(sig.action or "BUY").upper()
        is_buy = action == "BUY"
        mtf_str = str(sig.mtf_alignment or "").upper()
        trig_utc = _to_utc(sig.triggered_at) or _to_utc(sig.created_at)
        close_utc = _to_utc(sig.closed_at) or trig_utc
        created_utc = _to_utc(sig.created_at)

        # Normalize candles sorted chronologically
        bars: List[Tuple[datetime, float, float, float, float]] = []
        for c in m15_candles or []:
            ts = _norm_ts(c.get("timestamp"))
            if ts is not None:
                bars.append((ts, float(c["open"]), float(c["high"]), float(c["low"]), float(c["close"])))
        bars.sort(key=lambda x: x[0])

        # Find trigger candle & post-close candles (next 8 M15 bars = 2 hours after close)
        trig_bar = None
        post_close_bars: List[Tuple[datetime, float, float, float, float]] = []
        recent_ranges_pips: List[float] = []

        for bar in bars:
            ts, o, h, l, cl = bar
            if trig_utc and abs((ts - trig_utc).total_seconds()) <= 900:
                if trig_bar is None or abs((ts - trig_utc).total_seconds()) < abs((trig_bar[0] - trig_utc).total_seconds()):
                    trig_bar = bar
            if trig_utc and timedelta(hours=-3) <= (ts - trig_utc) <= timedelta(minutes=15):
                recent_ranges_pips.append(round((h - l) * 10.0, 1))
            if close_utc and timedelta(minutes=0) < (ts - close_utc) <= timedelta(hours=3):
                post_close_bars.append(bar)

        avg_m15_range = round(sum(recent_ranges_pips) / len(recent_ranges_pips), 1) if recent_ranges_pips else 0.0
        trig_body_pips = 0.0
        trig_range_pips = 0.0
        if trig_bar:
            _, o, h, l, cl = trig_bar
            trig_body_pips = round((cl - o) * 10.0, 1)
            trig_range_pips = round((h - l) * 10.0, 1)

        # Check if price reversed strongly in our predicted direction AFTER hitting SL (Stop-Hunt Sweep)
        post_sl_rebound_pips = 0.0
        if outcome == "SL_HIT" and post_close_bars:
            if is_buy:
                max_after = max(b[2] for b in post_close_bars)
                post_sl_rebound_pips = round(max(0.0, (max_after - sig.entry_price) * 10.0), 1)
            else:
                min_after = min(b[3] for b in post_close_bars)
                post_sl_rebound_pips = round(max(0.0, (sig.entry_price - min_after) * 10.0), 1)

        # WIN case: reinforce what worked!
        if outcome in ("TP1_HIT", "TP2_HIT", "TP3_HIT"):
            return {
                "cause_code": "VALID_CONFLUENCE_WIN",
                "cause_label": "Eksekusi Valid & Presisi",
                "severity": "POSITIVE",
                "diagnosis": (
                    f"Setup {action} ({sig.mtf_alignment or 'MTF'}) bereaksi bersih di Key Zone {sig.entry_zone} "
                    f"dengan puncak profit +{sig.max_favorable_pips:.0f}p dan drawdown terkendali -{sig.max_adverse_pips:.0f}p."
                ),
                "lesson": "Pertahankan disiplin tunggu konfluensi multi-TF dan proteksi trailing TP1→BEP.",
                "metrics": {
                    "avg_m15_range_pips": avg_m15_range,
                    "trigger_bar_body_pips": trig_body_pips,
                    "post_sl_rebound_pips": 0.0,
                },
            }

        if outcome == "EXPIRED":
            return {
                "cause_code": "UNFILLED_LIMIT",
                "cause_label": "Zona Tidak Terjemput",
                "severity": "NEUTRAL",
                "diagnosis": f"Harga tidak pernah kembali ke {sig.entry_zone} dalam 12 jam (0 pips — modal aman).",
                "lesson": "Zona disiplin tidak mengejar harga; jaga jarak zona realistis terhadap volatilitas sesi.",
                "metrics": {"avg_m15_range_pips": avg_m15_range},
            }

        # SL_HIT FORENSIC DIAGNOSIS (Priority ordered by root cause!)
        causes: List[str] = []
        primary_code = "TREND_BREAKOUT_AGAINST"
        primary_label = "Tembus Momentum Lawan"

        # 1. Check Revenge / Back-to-Back Entry right after previous SL
        is_revenge = False
        if prev_closed_trade and prev_closed_trade.outcome == "SL_HIT" and prev_closed_trade.closed_at and created_utc:
            gap_min = (created_utc - _to_utc(prev_closed_trade.closed_at)).total_seconds() / 60.0
            if -2.0 <= gap_min <= 45.0:
                is_revenge = True
                causes.append("re-entry terlalu cepat (<45 menit pasca SL sebelumnya tanpa jeda cooldown)")

        # 2. Check Blind Knife-Catch / Standing in front of opposing M15 impulse bar
        opposing_impulse = (
            (is_buy and trig_body_pips <= -45.0)
            or ((not is_buy) and trig_body_pips >= 45.0)
        )
        if opposing_impulse or (sig.max_favorable_pips <= 5.0 and trig_range_pips >= 85.0):
            causes.append(
                f"blind limit terjemput di tengah candle impuls lawan M15 ({trig_body_pips:+.0f}p / range {trig_range_pips:.0f}p) tanpa konfirmasi rejection"
            )

        # 3. Check MIXED / choppy MTF
        is_mixed = ("MIXED" in mtf_str) or ("3B / 3S" in mtf_str) or ("SIDEWAYS" in mtf_str)
        if is_mixed:
            causes.append(f"entry dipaksakan saat arah 7-TF belum kompak ({sig.mtf_alignment})")

        # 4. Check Stop-Hunt Sweep & Reverse (SL too tight for M15 ATR!)
        is_sweep_reverse = post_sl_rebound_pips >= 55.0
        sl_too_tight = (avg_m15_range > 0 and sig.risk_pips < avg_m15_range * 0.85)
        if is_sweep_reverse:
            causes.append(
                f"sapuan likuiditas (stop-hunt): setelah kena SL, harga justru berbalik +{post_sl_rebound_pips:.0f}p sesuai arah prediksi"
            )
        elif sl_too_tight:
            causes.append(
                f"SL (-{sig.risk_pips:.0f}p) lebih sempit dari rata-rata 1 candle M15 ({avg_m15_range:.0f}p)"
            )

        # 5. Check Premature Reversal (reached decent floating profit before reversing to SL)
        if sig.max_favorable_pips >= 40.0:
            causes.append(
                f"sempat profit +{sig.max_favorable_pips:.0f}p lalu berbalik kena SL sebelum menyentuh TP1 (+{sig.reward_tp1_pips:.0f}p)"
            )

        # Assign primary classification & concrete self-correction rule
        if is_revenge:
            primary_code = "REVENGE_BACK_TO_BACK_SL"
            primary_label = "Re-Entry Terlalu Cepat Pasca SL"
            lesson = "Aktifkan jeda cooldown 45 menit pasca SL dan tunggu struktur candle M15 baru tenang."
        elif opposing_impulse:
            primary_code = "BLIND_KNIFE_CATCH"
            primary_label = "Blind Limit Lawan Impuls M15"
            lesson = "Geser entry lebih dalam ke tepi luar zona (sweep edge) & hindari menghadang candle impuls >50p."
        elif is_mixed:
            primary_code = "MIXED_CHOP_ENTRY"
            primary_label = "Entry di Market Choppy (MIXED)"
            lesson = "Wajib tahan (WAIT) saat 7-TF MIXED; hanya buka posisi saat minimal 4/7 TF & M15 searah."
        elif is_sweep_reverse or sl_too_tight:
            primary_code = "SWEEP_AND_REVERSE"
            primary_label = "SL Tersapu Wick / Terlalu Sempit"
            lesson = "Perlebar buffer SL otomatis ke 0.85–1.0× ATR M15 (75–115p) di luar ekor likuiditas."
        elif sig.max_favorable_pips >= 40.0:
            primary_code = "PREMATURE_REVERSAL"
            primary_label = "Berbalik Sebelum TP1"
            lesson = "Dekatkan TP1 ke 1.05–1.20× SL agar 40% lot & BEP lebih cepat diamankan."
        else:
            primary_code = "TREND_BREAKOUT_AGAINST"
            primary_label = "Tembus Tren / Breakout Lawan"
            lesson = "Ikuti arah momentum M15+H1 dominan; jangan pasang limit melawan arah breakout kuat."

        diag_text = (
            "Penyebab SL terdeteksi: " + "; ".join(causes) + "."
            if causes
            else f"Setup {action} di {sig.entry_zone} tertembus momentum lawan (-{sig.risk_pips:.0f}p) dengan MFE +{sig.max_favorable_pips:.0f}p."
        )

        return {
            "cause_code": primary_code,
            "cause_label": primary_label,
            "severity": "WARNING",
            "diagnosis": diag_text,
            "lesson": lesson,
            "metrics": {
                "avg_m15_range_pips": avg_m15_range,
                "trigger_bar_body_pips": trig_body_pips,
                "trigger_bar_range_pips": trig_range_pips,
                "post_sl_rebound_pips": post_sl_rebound_pips,
            },
        }

    @classmethod
    def build_adaptive_learning_profile(
        cls,
        db: Session,
        symbol: str = "XAUUSD",
    ) -> Dict[str, Any]:
        """
        Reads recent closed LIVE trades & their post-mortems to compute live self-correction
        parameters fed into BOTH Gemini/OpenRouter AI prompts AND Quantitative Guardrails!
        """
        sym = symbol.upper()
        closed_rows = (
            db.query(TradeSignalHistory)
            .filter(
                TradeSignalHistory.symbol == sym,
                TradeSignalHistory.source_type == "LIVE",
                TradeSignalHistory.is_closed == True,
                TradeSignalHistory.outcome.in_(["SL_HIT", "TP1_HIT", "TP2_HIT", "TP3_HIT"]),
            )
            .order_by(desc(TradeSignalHistory.closed_at))
            .limit(10)
            .all()
        )

        # Count consecutive SL streak from newest backwards
        consecutive_sl = 0
        last_sl_row: Optional[TradeSignalHistory] = None
        for r in closed_rows:
            if r.outcome == "SL_HIT":
                if last_sl_row is None:
                    last_sl_row = r
                consecutive_sl += 1
            else:
                break

        cause_counts: Dict[str, int] = {}
        recent_lessons: List[str] = []
        mfe_zero_sls = 0
        mixed_sls = 0
        total_sls = 0
        total_wins = 0

        for r in closed_rows:
            if r.outcome == "SL_HIT":
                total_sls += 1
                if (r.max_favorable_pips or 0.0) <= 5.0:
                    mfe_zero_sls += 1
                if "MIXED" in str(r.mtf_alignment or "").upper():
                    mixed_sls += 1
            else:
                total_wins += 1

            pm = {}
            if getattr(r, "post_mortem_json", None):
                try:
                    pm = json.loads(r.post_mortem_json)
                except Exception:
                    pm = {}
            code = pm.get("cause_code")
            if code and r.outcome == "SL_HIT":
                cause_counts[code] = cause_counts.get(code, 0) + 1
            lesson = pm.get("lesson")
            if lesson and r.outcome == "SL_HIT" and lesson not in recent_lessons:
                recent_lessons.append(lesson)

        # Compute live adaptive adjustments based on actual failure patterns!
        # 1. Cooldown check: if last trade hit SL < 45 minutes ago (60 min if >= 2 consecutive SL)
        cooldown_minutes = 60 if consecutive_sl >= 2 else 45
        in_cooldown = False
        cooldown_remaining_min = 0
        last_sl_action: Optional[str] = None
        if last_sl_row and last_sl_row.closed_at:
            last_sl_action = last_sl_row.action
            elapsed_min = (datetime.now(timezone.utc) - _to_utc(last_sl_row.closed_at)).total_seconds() / 60.0
            if 0 <= elapsed_min < cooldown_minutes:
                in_cooldown = True
                cooldown_remaining_min = max(1, int(round(cooldown_minutes - elapsed_min)))

        # 2. Adaptive SL multiplier boost when suffering sweep/knife-catch SL hits
        sl_buffer_mult = 1.0
        if consecutive_sl >= 2 or mfe_zero_sls >= 2 or cause_counts.get("SWEEP_AND_REVERSE", 0) >= 1:
            sl_buffer_mult = 1.28  # Expand SL buffer cleanly outside M15 sweep wicks (up to 110-115p in volatile sessions)
        elif consecutive_sl == 1:
            sl_buffer_mult = 1.15

        # 3. Strict Trend-Alignment Filter (block MIXED chop entries!)
        block_mixed_chop = (mixed_sls >= 1) or (consecutive_sl >= 2)

        # 4. Deeper Outer-Edge Entry Shift (avoid front-edge fills during waterfall sweeps)
        use_outer_edge_entry = (mfe_zero_sls >= 2) or (cause_counts.get("BLIND_KNIFE_CATCH", 0) >= 1)

        # 5. Faster TP1 Lock (easier to reach TP1 & secure BEP during recovery from SL streak)
        tp1_ratio = 1.10 if consecutive_sl >= 2 else 1.25

        active_adjustments: List[str] = []
        if sl_buffer_mult > 1.0:
            active_adjustments.append(f"Buffer SL Adaptif ×{sl_buffer_mult:.2f} (aman di luar sapuan M15 ATR)")
        if block_mixed_chop:
            active_adjustments.append("Filter Anti-Choppy Aktif (tahan WAIT saat 7-TF MIXED)")
        if use_outer_edge_entry:
            active_adjustments.append("Entry Tepi Luar Zona (hindari terjemput candle impuls)")
        if consecutive_sl >= 1:
            active_adjustments.append(f"Cooldown Pasca-SL {cooldown_minutes} menit (anti revenge-entry)")
        if tp1_ratio <= 1.15:
            active_adjustments.append("TP1 Cepat (1.10× SL) agar profit 40% & BEP cepat terkunci")

        if total_sls == 0 and total_wins == 0:
            summary = "Belum ada trade selesai — sistem siap mencatat & mengevaluasi otomatis begitu ada SL atau TP."
        elif consecutive_sl >= 2:
            summary = (
                f"Evaluasi mandiri mendeteksi {consecutive_sl}× SL beruntun ({mfe_zero_sls}× langsung terjemput impuls MFE 0p"
                f"{f', {mixed_sls}× saat market MIXED' if mixed_sls else ''}). "
                f"Engine otomatis mengaktifkan mode defensif: larang entry di market MIXED, geser entry ke tepi luar zona, "
                f"perlebar buffer SL di luar sapuan M15, dan wajib jeda {cooldown_minutes} menit pasca SL."
            )
        elif total_sls > total_wins:
            summary = (
                f"Dari {total_wins + total_sls} trade selesai ({total_wins}W/{total_sls}L), evaluasi mandiri menyesuaikan "
                f"buffer SL adaptif M15 dan memperketat filter konfluensi agar tidak melawan candle impuls."
            )
        else:
            summary = (
                f"Performa terjaga ({total_wins}W/{total_sls}L). Sistem terus mengevaluasi setiap hasil SL & TP "
                f"secara mandiri untuk menjaga presisi Key Zone."
            )

        return {
            "analyzed_trades": len(closed_rows),
            "consecutive_sl": consecutive_sl,
            "total_recent_wins": total_wins,
            "total_recent_losses": total_sls,
            "mfe_zero_sl_count": mfe_zero_sls,
            "mixed_sl_count": mixed_sls,
            "in_post_sl_cooldown": in_cooldown,
            "cooldown_remaining_min": cooldown_remaining_min,
            "last_sl_action": last_sl_action,
            "sl_buffer_mult": sl_buffer_mult,
            "block_mixed_chop": block_mixed_chop,
            "use_outer_edge_entry": use_outer_edge_entry,
            "tp1_ratio": tp1_ratio,
            "cause_counts": cause_counts,
            "active_adjustments": active_adjustments,
            "recent_lessons": recent_lessons[:4],
            "summary": summary,
        }
