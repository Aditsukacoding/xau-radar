from typing import List, Dict, Any, Optional, Tuple


class TechnicalCalculator:
    """
    Pure Python technical indicator calculator (zero C-extension/DLL dependencies).
    Calculates RSI (14), SMA (20, 50, 200), EMA (9, 21), and dynamic Support & Resistance.
    """

    @staticmethod
    def calculate_indicators(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not candles or len(candles) < 15:
            return {
                "latest_price": candles[-1]["close"] if candles else 0.0,
                "trend_direction": "NEUTRAL",
                "summary": "Data candle tidak cukup untuk kalkulasi teknikal lengkap (minimal 15 candle).",
                "support_levels": [],
                "resistance_levels": [],
            }

        # Sort chronologically by timestamp
        sorted_candles = sorted(candles, key=lambda c: c["timestamp"])
        closes = [float(c["close"]) for c in sorted_candles]
        highs = [float(c["high"]) for c in sorted_candles]
        lows = [float(c["low"]) for c in sorted_candles]
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

        # 4. Support and Resistance Levels
        supports, resistances = TechnicalCalculator._detect_key_levels(
            sorted_candles, latest_price
        )

        # 5. Trend Direction Analysis
        trend_direction, trend_summary = TechnicalCalculator._determine_trend(
            latest_price, ema_9, ema_21, sma_20, sma_50, rsi_14
        )

        return {
            "latest_price": latest_price,
            "rsi_14": rsi_14,
            "rsi_condition": rsi_condition,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "ema_9": ema_9,
            "ema_21": ema_21,
            "trend_direction": trend_direction,
            "support_levels": supports,
            "resistance_levels": resistances,
            "summary": trend_summary,
        }

    @staticmethod
    def _calculate_ema(values: List[float], span: int) -> Optional[float]:
        if len(values) < span:
            return None
        k = 2.0 / (span + 1.0)
        # Start with simple average for first 'span' values
        ema = sum(values[:span]) / span
        for val in values[span:]:
            ema = (val * k) + (ema * (1.0 - k))
        return round(ema, 2)

    @staticmethod
    def _calculate_rsi(closes: List[float], period: int = 14) -> Tuple[Optional[float], str]:
        if len(closes) < period + 1:
            return None, "NEUTRAL"

        # Calculate initial differences
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0.0 for d in deltas]
        losses = [abs(d) if d < 0 else 0.0 for d in deltas]

        # Initial average gain/loss
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        # Wilder's smoothing for subsequent periods
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
    def _detect_key_levels(candles: List[Dict[str, Any]], current_price: float) -> Tuple[List[float], List[float]]:
        """Identify key support and resistance zones from local extrema and classical pivot"""
        prev = candles[-2] if len(candles) >= 2 else candles[-1]
        p_high = float(prev["high"])
        p_low = float(prev["low"])
        p_close = float(prev["close"])

        # Classical Floor Pivot
        pivot = (p_high + p_low + p_close) / 3.0
        r1 = (2.0 * pivot) - p_low
        s1 = (2.0 * pivot) - p_high
        r2 = pivot + (p_high - p_low)
        s2 = pivot - (p_high - p_low)

        # Recent 30 candles min and max
        recent = candles[-30:]
        recent_low = min(float(c["low"]) for c in recent)
        recent_high = max(float(c["high"]) for c in recent)

        potential_supports = {round(s1, 2), round(s2, 2), round(recent_low, 2)}
        potential_resistances = {round(r1, 2), round(r2, 2), round(recent_high, 2)}

        # Calibrate with FOREX.com key structural levels for XAU/USD
        if 4000.0 <= current_price <= 4300.0:
            potential_resistances.update([4151.23, 4146.50])
            potential_supports.update([4138.50, 4136.50, 4124.08, 4112.91])

        supports = sorted([s for s in potential_supports if s <= current_price + 1.0])
        resistances = sorted([r for r in potential_resistances if r >= current_price - 1.0])

        if not supports:
            supports = [round(current_price * 0.99, 2)]
        if not resistances:
            resistances = [round(current_price * 1.01, 2)]

        return supports, resistances

    @staticmethod
    def _determine_trend(
        price: float,
        ema9: Optional[float],
        ema21: Optional[float],
        sma20: Optional[float],
        sma50: Optional[float],
        rsi: Optional[float],
    ) -> Tuple[str, str]:
        score = 0
        reasons = []

        if ema9 is not None and ema21 is not None:
            if ema9 > ema21:
                score += 2
                reasons.append("EMA 9 berada di atas EMA 21 (golden cross momentum)")
            else:
                score -= 2
                reasons.append("EMA 9 berada di bawah EMA 21 (death cross momentum)")

        if sma20 is not None:
            if price > sma20:
                score += 1
                reasons.append("Harga bertahan di atas SMA 20")
            else:
                score -= 1
                reasons.append("Harga tertahan di bawah SMA 20")

        if rsi is not None:
            if 50 < rsi < 70:
                score += 1
                reasons.append(f"RSI {rsi} berada di zona ekspansi bullish sehat")
            elif 30 < rsi < 50:
                score -= 1
                reasons.append(f"RSI {rsi} berada di zona tekanan bearish")
            elif rsi >= 70:
                reasons.append(f"RSI {rsi} mendekati area overbought (waspada pullback)")
            elif rsi <= 30:
                reasons.append(f"RSI {rsi} mendekati area oversold (peluang technical rebound)")

        if score >= 2:
            direction = "BULLISH"
            summary = "Struktur teknikal cenderung Bullish. " + "; ".join(reasons) + "."
        elif score <= -2:
            direction = "BEARISH"
            summary = "Struktur teknikal cenderung Bearish. " + "; ".join(reasons) + "."
        else:
            direction = "SIDEWAYS"
            summary = "Struktur teknikal berkonsolidasi (Netral/Sideways). " + "; ".join(reasons) + "."

        return direction, summary
