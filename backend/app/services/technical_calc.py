from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple


class TechnicalCalculator:
    """
    Pure Python institutional technical & scalping indicator calculator.
    Calculates RSI (14), ATR (14), SMA (20, 50, 200), EMA (9, 21),
    fractal Swing High/Low structure, price-action momentum, active market session,
    and dynamic Support & Resistance levels.
    """

    @staticmethod
    def detect_active_session(now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """Detects active global XAU/USD trading session and typical volatility profile."""
        dt = now_utc or datetime.now(timezone.utc)
        hour_utc = dt.hour

        if 12 <= hour_utc < 16:
            return {
                "name": "London-NY Killzone",
                "volatility": "HIGH",
                "wib_window": "19:00 - 23:00 WIB",
                "atr_sl_mult": 1.35,
            }
        if 7 <= hour_utc < 12:
            return {
                "name": "London Session",
                "volatility": "MEDIUM_HIGH",
                "wib_window": "14:00 - 19:00 WIB",
                "atr_sl_mult": 1.25,
            }
        if 16 <= hour_utc < 21:
            return {
                "name": "New York Session",
                "volatility": "MEDIUM_HIGH",
                "wib_window": "23:00 - 04:00 WIB",
                "atr_sl_mult": 1.25,
            }
        if 0 <= hour_utc < 7:
            return {
                "name": "Asian Session",
                "volatility": "LOW_MEDIUM",
                "wib_window": "07:00 - 14:00 WIB",
                "atr_sl_mult": 1.10,
            }
        return {
            "name": "NY Rollover / Thin Liquidity",
            "volatility": "LOW",
            "wib_window": "04:00 - 07:00 WIB",
            "atr_sl_mult": 1.15,
        }

    @staticmethod
    def calculate_indicators(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        session_info = TechnicalCalculator.detect_active_session()

        if not candles or len(candles) < 15:
            latest = round(float(candles[-1]["close"]), 2) if candles else 0.0
            return {
                "latest_price": latest,
                "atr_14": 3.5,
                "atr_pips": 35.0,
                "trend_direction": "NEUTRAL",
                "price_action": "INSUFFICIENT_DATA",
                "session_name": session_info["name"],
                "session_volatility": session_info["volatility"],
                "swing_highs": [],
                "swing_lows": [],
                "summary": "Data candle tidak cukup untuk kalkulasi teknikal lengkap (minimal 15 candle).",
                "support_levels": [],
                "resistance_levels": [],
            }

        # Sort chronologically by timestamp
        sorted_candles = sorted(candles, key=lambda c: c["timestamp"])
        closes = [float(c["close"]) for c in sorted_candles]
        latest_price = round(closes[-1], 2)
        n = len(closes)

        # 1. Simple Moving Averages (SMA)
        sma_20 = round(sum(closes[-20:]) / 20, 2) if n >= 20 else None
        sma_50 = round(sum(closes[-50:]) / 50, 2) if n >= 50 else None
        sma_200 = round(sum(closes[-200:]) / 200, 2) if n >= 200 else None

        # 2. Exponential Moving Averages (EMA)
        ema_9 = TechnicalCalculator._calculate_ema(closes, 9)
        ema_21 = TechnicalCalculator._calculate_ema(closes, 21)

        # 3. Relative Strength Index (RSI 14)
        rsi_14, rsi_condition = TechnicalCalculator._calculate_rsi(closes, period=14)

        # 4. Average True Range (ATR 14) for dynamic volatility-calibrated SL/TP
        atr_14 = TechnicalCalculator._calculate_atr(sorted_candles, period=14)
        atr_pips = round(atr_14 * 10.0, 1)

        # 5. Fractal Swing Highs & Swing Lows
        swing_lows, swing_highs = TechnicalCalculator._detect_swing_points(sorted_candles, latest_price)

        # 6. Dynamic Support and Resistance Levels (pure market structure, zero hardcoded legacy levels)
        supports, resistances = TechnicalCalculator._detect_key_levels(
            sorted_candles, latest_price, swing_lows, swing_highs, atr_14
        )

        # 7. Micro Price Action Signal (last 3 candles)
        price_action, pa_note = TechnicalCalculator._detect_price_action(sorted_candles, ema_9, ema_21)

        # 8. Trend Direction Analysis
        trend_direction, trend_summary = TechnicalCalculator._determine_trend(
            latest_price, ema_9, ema_21, sma_20, sma_50, rsi_14, pa_note
        )

        return {
            "latest_price": latest_price,
            "rsi_14": rsi_14,
            "rsi_condition": rsi_condition,
            "atr_14": atr_14,
            "atr_pips": atr_pips,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "ema_9": ema_9,
            "ema_21": ema_21,
            "trend_direction": trend_direction,
            "price_action": price_action,
            "price_action_note": pa_note,
            "session_name": session_info["name"],
            "session_volatility": session_info["volatility"],
            "swing_lows": swing_lows,
            "swing_highs": swing_highs,
            "support_levels": supports,
            "resistance_levels": resistances,
            "summary": trend_summary,
        }

    @staticmethod
    def _calculate_ema(values: List[float], span: int) -> Optional[float]:
        if len(values) < span:
            return None
        k = 2.0 / (span + 1.0)
        ema = sum(values[:span]) / span
        for val in values[span:]:
            ema = (val * k) + (ema * (1.0 - k))
        return round(ema, 2)

    @staticmethod
    def _calculate_atr(candles: List[Dict[str, Any]], period: int = 14) -> float:
        if len(candles) < 2:
            return 3.50
        true_ranges: List[float] = []
        for i in range(1, len(candles)):
            high = float(candles[i]["high"])
            low = float(candles[i]["low"])
            prev_close = float(candles[i - 1]["close"])
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)

        if not true_ranges:
            return 3.50

        if len(true_ranges) < period:
            atr = sum(true_ranges) / len(true_ranges)
        else:
            atr = sum(true_ranges[:period]) / period
            for tr in true_ranges[period:]:
                atr = ((atr * (period - 1)) + tr) / period

        return round(max(1.20, atr), 2)

    @staticmethod
    def _calculate_rsi(closes: List[float], period: int = 14) -> Tuple[Optional[float], str]:
        if len(closes) < period + 1:
            return None, "NEUTRAL"

        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0.0 for d in deltas]
        losses = [abs(d) if d < 0 else 0.0 for d in deltas]

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))

        rsi_val = round(rsi, 2)
        if rsi_val >= 70:
            cond = "OVERBOUGHT"
        elif rsi_val <= 30:
            cond = "OVERSOLD"
        else:
            cond = "NEUTRAL"

        return rsi_val, cond

    @staticmethod
    def _detect_swing_points(
        candles: List[Dict[str, Any]],
        current_price: float,
        window: int = 2,
    ) -> Tuple[List[float], List[float]]:
        """Detects authentic local fractal swing lows and swing highs from OHLCV candles."""
        recent = candles[-50:] if len(candles) > 50 else candles
        n = len(recent)
        lows: List[float] = []
        highs: List[float] = []

        if n >= (window * 2 + 1):
            for i in range(window, n - window):
                c_low = float(recent[i]["low"])
                c_high = float(recent[i]["high"])
                if all(c_low <= float(recent[j]["low"]) for j in range(i - window, i + window + 1) if j != i):
                    if c_low < current_price:
                        lows.append(round(c_low, 2))
                if all(c_high >= float(recent[j]["high"]) for j in range(i - window, i + window + 1) if j != i):
                    if c_high > current_price:
                        highs.append(round(c_high, 2))

        # Deduplicate close clusters (within $1.20) keeping nearest structural swings
        def cluster_levels(levels: List[float], reverse: bool) -> List[float]:
            ordered = sorted(set(levels), reverse=reverse)
            clustered: List[float] = []
            for lv in ordered:
                if not clustered or abs(lv - clustered[-1]) >= 1.20:
                    clustered.append(lv)
            return clustered[:4]

        return cluster_levels(lows, reverse=True), cluster_levels(highs, reverse=False)

    @staticmethod
    def _detect_key_levels(
        candles: List[Dict[str, Any]],
        current_price: float,
        swing_lows: List[float],
        swing_highs: List[float],
        atr_14: float,
    ) -> Tuple[List[float], List[float]]:
        """Combines authentic fractal swings, recent range boundaries, and classical floor pivots."""
        prev = candles[-2] if len(candles) >= 2 else candles[-1]
        p_high = float(prev["high"])
        p_low = float(prev["low"])
        p_close = float(prev["close"])

        pivot = (p_high + p_low + p_close) / 3.0
        r1 = (2.0 * pivot) - p_low
        s1 = (2.0 * pivot) - p_high
        r2 = pivot + (p_high - p_low)
        s2 = pivot - (p_high - p_low)

        recent = candles[-30:]
        recent_low = min(float(c["low"]) for c in recent)
        recent_high = max(float(c["high"]) for c in recent)

        potential_supports = set(swing_lows) | {round(s1, 2), round(s2, 2), round(recent_low, 2)}
        potential_resistances = set(swing_highs) | {round(r1, 2), round(r2, 2), round(recent_high, 2)}

        # Keep levels strictly below/above current_price within sensible intraday range
        supports = sorted([s for s in potential_supports if (current_price - atr_14 * 12) <= s < current_price - 0.30], reverse=True)
        resistances = sorted([r for r in potential_resistances if current_price + 0.30 < r <= (current_price + atr_14 * 12)])

        # Deduplicate tightly packed levels (< $1.50 apart)
        def dedup(lvls: List[float]) -> List[float]:
            out: List[float] = []
            for v in lvls:
                if not out or abs(v - out[-1]) >= 1.50:
                    out.append(v)
            return out[:4]

        supports = dedup(supports)
        resistances = dedup(resistances)

        if not supports:
            supports = [round(current_price - max(3.5, atr_14 * 1.4), 2), round(current_price - max(8.0, atr_14 * 2.8), 2)]
        if not resistances:
            resistances = [round(current_price + max(3.5, atr_14 * 1.4), 2), round(current_price + max(8.0, atr_14 * 2.8), 2)]

        return supports, resistances

    @staticmethod
    def _detect_price_action(
        candles: List[Dict[str, Any]],
        ema9: Optional[float],
        ema21: Optional[float],
    ) -> Tuple[str, str]:
        """Reads the latest 3 candles for scalping price-action confirmation (rejection, engulfing, impulse)."""
        if len(candles) < 3:
            return "CONSOLIDATION", "Aksi harga konsolidasi ketat"

        c_prev = candles[-2]
        c_last = candles[-1]

        o1, h1, l1, cl1 = float(c_prev["open"]), float(c_prev["high"]), float(c_prev["low"]), float(c_prev["close"])
        o2, h2, l2, cl2 = float(c_last["open"]), float(c_last["high"]), float(c_last["low"]), float(c_last["close"])

        body2 = abs(cl2 - o2)
        range2 = max(h2 - l2, 0.01)
        upper_wick = h2 - max(o2, cl2)
        lower_wick = min(o2, cl2) - l2

        # Bullish Pinbar / Demand Sweep
        if lower_wick >= range2 * 0.50 and cl2 >= o2 - (range2 * 0.15):
            return "BULLISH_REJECTION", "Ekor bawah panjang (rejection buyer / sweep likuiditas demand)"

        # Bearish Pinbar / Supply Sweep
        if upper_wick >= range2 * 0.50 and cl2 <= o2 + (range2 * 0.15):
            return "BEARISH_REJECTION", "Ekor atas panjang (rejection seller / sweep likuiditas supply)"

        # Bullish Engulfing / Strong Impulse
        if cl2 > o2 and cl1 < o1 and cl2 > o1 and body2 >= abs(cl1 - o1):
            return "BULLISH_ENGULFING", "Pola Bullish Engulfing aktif mengonfirmasi dorongan buyer"

        # Bearish Engulfing / Strong Impulse
        if cl2 < o2 and cl1 > o1 and cl2 < o1 and body2 >= abs(cl1 - o1):
            return "BEARISH_ENGULFING", "Pola Bearish Engulfing aktif mengonfirmasi tekanan seller"

        # Momentum displacement
        if cl2 > o2 and body2 >= range2 * 0.60:
            return "BULLISH_IMPULSE", "Candle dorongan bullish kuat (momentum buyer dominan)"
        if cl2 < o2 and body2 >= range2 * 0.60:
            return "BEARISH_IMPULSE", "Candle tekanan bearish kuat (momentum seller dominan)"

        # Pullback to EMA zone
        if ema9 is not None and ema21 is not None:
            if min(ema9, ema21) - 1.5 <= cl2 <= max(ema9, ema21) + 1.5:
                return "EMA_PULLBACK", "Harga sedang retest zona dinamis EMA 9/21 (area entry pullback ideal)"

        return "CONSOLIDATION", "Pergerakan kompresi menyempit menunggu ekspansi candle berikutnya"

    @staticmethod
    def _determine_trend(
        price: float,
        ema9: Optional[float],
        ema21: Optional[float],
        sma20: Optional[float],
        sma50: Optional[float],
        rsi: Optional[float],
        pa_note: str = "",
    ) -> Tuple[str, str]:
        score = 0
        reasons = []

        if ema9 is not None and ema21 is not None:
            if ema9 > ema21:
                score += 2
                reasons.append("EMA 9 di atas EMA 21 (struktur naik)")
            else:
                score -= 2
                reasons.append("EMA 9 di bawah EMA 21 (struktur turun)")

        if sma20 is not None:
            if price > sma20:
                score += 1
                reasons.append("harga bertahan di atas SMA 20")
            else:
                score -= 1
                reasons.append("harga tertahan di bawah SMA 20")

        if rsi is not None:
            if 52 <= rsi < 70:
                score += 1
                reasons.append(f"RSI {rsi} di zona momentum bullish")
            elif 30 < rsi <= 48:
                score -= 1
                reasons.append(f"RSI {rsi} di zona tekanan bearish")
            elif rsi >= 70:
                reasons.append(f"RSI {rsi} overbought (waspada pullback)")
            elif rsi <= 30:
                reasons.append(f"RSI {rsi} oversold (potensi pantulan cepat)")

        if pa_note:
            reasons.append(pa_note)

        if score >= 2:
            direction = "BULLISH"
            summary = "Struktur teknikal Bullish: " + "; ".join(reasons) + "."
        elif score <= -2:
            direction = "BEARISH"
            summary = "Struktur teknikal Bearish: " + "; ".join(reasons) + "."
        else:
            direction = "SIDEWAYS"
            summary = "Struktur teknikal Sideways/Range: " + "; ".join(reasons) + "."

        return direction, summary

    @staticmethod
    def analyze_mtf_confluence(
        mtf_map: Dict[str, Dict[str, Any]],
        curr_price: float,
    ) -> Dict[str, Any]:
        """
        Synthesizes all 7 timeframes (M1, M5, M15, M30, H1, H4, D1) into:
        - Per-timeframe directional & S/R comparison matrix (mtf_overview)
        - Top-Down Alignment (HTF D1/H4/H1 vs ITF M30/M15 vs LTF M5/M1)
        - Cross-Timeframe Confluence Support & Resistance clusters (overlapping zones across TFs)
        """
        ordered_tfs = [
            ("1m", "M1", 0.7),
            ("5m", "M5", 1.0),
            ("15m", "M15", 1.4),
            ("30m", "M30", 1.6),
            ("1h", "H1", 2.0),
            ("4h", "H4", 2.5),
            ("1d", "D1", 3.0),
        ]

        overview: List[Dict[str, Any]] = []
        all_sups: List[Tuple[float, str, float]] = []
        all_res: List[Tuple[float, str, float]] = []

        bull_cnt = 0
        bear_cnt = 0
        side_cnt = 0
        weighted_dir = 0.0
        total_weight = 0.0

        def dir_val(t: str) -> float:
            u = str(t or "").upper()
            return 1.0 if u == "BULLISH" else (-1.0 if u == "BEARISH" else 0.0)

        for key, label, weight in ordered_tfs:
            td = mtf_map.get(key) or {}
            trend = str(td.get("trend_direction", "SIDEWAYS")).upper()
            if trend not in ("BULLISH", "BEARISH", "SIDEWAYS"):
                trend = "SIDEWAYS"

            if trend == "BULLISH":
                bull_cnt += 1
            elif trend == "BEARISH":
                bear_cnt += 1
            else:
                side_cnt += 1

            weighted_dir += dir_val(trend) * weight
            total_weight += weight

            sups = [float(x) for x in (td.get("support_levels") or []) if float(x) < curr_price]
            ress = [float(x) for x in (td.get("resistance_levels") or []) if float(x) > curr_price]
            sw_lows = [float(x) for x in (td.get("swing_lows") or []) if float(x) < curr_price]
            sw_highs = [float(x) for x in (td.get("swing_highs") or []) if float(x) > curr_price]

            nearest_sup = round(max(sups), 2) if sups else round(curr_price - 5.0, 2)
            nearest_res = round(min(ress), 2) if ress else round(curr_price + 5.0, 2)

            for s in set(sups[:2] + sw_lows[:2]):
                all_sups.append((round(s, 2), label, weight))
            for r in set(ress[:2] + sw_highs[:2]):
                all_res.append((round(r, 2), label, weight))

            overview.append({
                "tf": label,
                "trend": trend,
                "rsi": round(float(td["rsi_14"]), 1) if td.get("rsi_14") is not None else None,
                "atr_pips": round(float(td.get("atr_pips", 0.0)), 1),
                "sup": nearest_sup,
                "res": nearest_res,
                "pa": str(td.get("price_action", "CONSOLIDATION")),
            })

        # Cluster overlapping levels across timeframes (within $3.20 band)
        def build_clusters(points: List[Tuple[float, str, float]], sort_desc: bool) -> List[Dict[str, Any]]:
            if not points:
                return []
            ordered = sorted(points, key=lambda x: x[0], reverse=sort_desc)
            clusters: List[List[Tuple[float, str, float]]] = []
            for pt in ordered:
                placed = False
                for cl in clusters:
                    avg_p = sum(x[0] for x in cl) / len(cl)
                    if abs(pt[0] - avg_p) <= 3.20:
                        cl.append(pt)
                        placed = True
                        break
                if not placed:
                    clusters.append([pt])

            formatted: List[Dict[str, Any]] = []
            for cl in clusters:
                tfs_unique = list(dict.fromkeys(x[1] for x in cl))
                w_sum = sum(x[2] for x in cl)
                w_avg = round(sum(x[0] * x[2] for x in cl) / w_sum, 2) if w_sum > 0 else round(cl[0][0], 2)
                formatted.append({
                    "price": w_avg,
                    "low": round(min(x[0] for x in cl), 2),
                    "high": round(max(x[0] for x in cl), 2),
                    "timeframes": tfs_unique,
                    "tf_count": len(tfs_unique),
                    "weight": round(w_sum, 2),
                })

            # Prioritize multi-TF clusters close to live price (proximity-weighted confluence)
            formatted.sort(
                key=lambda c: (
                    c["tf_count"] >= 2,
                    c["weight"] / (1.0 + abs(c["price"] - curr_price) / 20.0),
                ),
                reverse=True,
            )
            return formatted[:4]

        conf_supports = build_clusters(all_sups, sort_desc=True)
        conf_resistances = build_clusters(all_res, sort_desc=False)

        # Tiered perspective comparison: HTF (D1/H4/H1) vs ITF (M30/M15) vs LTF (M5/M1)
        def group_bias(keys: List[str]) -> str:
            sc = sum(dir_val((mtf_map.get(k) or {}).get("trend_direction", "SIDEWAYS")) for k in keys)
            return "BULLISH" if sc >= 1 else ("BEARISH" if sc <= -1 else "SIDEWAYS")

        htf_bias = group_bias(["1d", "4h", "1h"])
        itf_bias = group_bias(["30m", "15m"])
        ltf_bias = group_bias(["5m", "1m"])

        mtf_score = round(weighted_dir / total_weight, 3) if total_weight > 0 else 0.0

        if bull_cnt >= 5:
            alignment_label = f"{bull_cnt}/7 BULLISH • Selaras Kuat"
        elif bear_cnt >= 5:
            alignment_label = f"{bear_cnt}/7 BEARISH • Selaras Kuat"
        elif htf_bias != ltf_bias and htf_bias != "SIDEWAYS" and ltf_bias != "SIDEWAYS":
            alignment_label = f"HTF {htf_bias} • LTF {ltf_bias} (Pullback)"
        elif bull_cnt > bear_cnt:
            alignment_label = f"{bull_cnt}/7 BULLISH • Moderat"
        elif bear_cnt > bull_cnt:
            alignment_label = f"{bear_cnt}/7 BEARISH • Moderat"
        else:
            alignment_label = f"MIXED ({bull_cnt}B / {bear_cnt}S / {side_cnt}R)"

        top_sup_str = (
            f"${conf_supports[0]['price']:.2f} ({'+'.join(conf_supports[0]['timeframes'])})"
            if conf_supports
            else "-"
        )
        top_res_str = (
            f"${conf_resistances[0]['price']:.2f} ({'+'.join(conf_resistances[0]['timeframes'])})"
            if conf_resistances
            else "-"
        )

        confluence_note = (
            f"Top-Down {alignment_label} (HTF {htf_bias} | ITF {itf_bias} | LTF {ltf_bias}). "
            f"Zona konfluensi kuat: Support {top_sup_str} & Resistance {top_res_str}."
        )

        return {
            "overview": overview,
            "htf_bias": htf_bias,
            "itf_bias": itf_bias,
            "ltf_bias": ltf_bias,
            "bullish_count": bull_cnt,
            "bearish_count": bear_cnt,
            "sideways_count": side_cnt,
            "mtf_score": mtf_score,
            "alignment_label": alignment_label,
            "confluence_supports": conf_supports,
            "confluence_resistances": conf_resistances,
            "confluence_note": confluence_note,
        }
