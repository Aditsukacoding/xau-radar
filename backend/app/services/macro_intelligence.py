"""
Institutional Macro, Intermarket, Geopolitical & Historical News Reaction Engine.

Provides 4 pure-data intelligence layers for XAU/USD:
1. Numeric Economic Surprise Evaluator (Actual vs Forecast vs Previous with accurate USD/Gold polarity)
2. Live Intermarket Feed (DXY Dollar Index, US10Y Treasury Yield, WTI Crude Oil via Yahoo Finance)
3. Historical Market Reaction Tracker (cross-references released economic events with real XAU/USD 1H candles)
4. Time-Decayed, Theme-Classified, Negation-Aware Geopolitical & Macro News Synthesizer
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
import httpx

logger = logging.getLogger(__name__)

WIB = timezone(timedelta(hours=7))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}


class MacroIntelligenceService:
    # In-memory cache for live intermarket feed (3-minute TTL)
    _intermarket_cache: Optional[Dict[str, Any]] = None
    _intermarket_cache_ts: float = 0.0
    _INTERMARKET_TTL: float = 180.0
    _recent_tv_usd_cache: List[Dict[str, Any]] = []
    _recent_tv_usd_ts: float = 0.0

    # Indicators where HIGHER Actual = WEAKER USD = BULLISH GOLD (inverse polarity)
    INVERSE_USD_KEYWORDS = (
        "unemployment",
        "jobless",
        "initial claims",
        "continuing claims",
        "challenger job cuts",
        "layoffs",
        "trade deficit",
    )

    # Indicators where HIGHER Actual = STRONGER USD / HAWKISH FED = BEARISH GOLD
    PRO_USD_KEYWORDS = (
        "cpi",
        "core cpi",
        "pce",
        "core pce",
        "ppi",
        "inflation",
        "non-farm",
        "nonfarm",
        "payroll",
        "nfp",
        "adp",
        "jolts",
        "average hourly",
        "wage",
        "gdp",
        "retail sales",
        "ism",
        "pmi",
        "durable goods",
        "consumer confidence",
        "michigan",
        "housing",
        "building permits",
        "home sales",
        "industrial production",
        "interest rate",
        "fed funds",
        "rate decision",
        "empire state",
        "philly fed",
        "cb consumer",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. NUMERIC ECONOMIC SURPRISE EVALUATOR (ACTUAL vs FORECAST vs PREVIOUS)
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def parse_numeric_value(raw: Optional[str]) -> Optional[float]:
        """Parses formatted economic strings ('2.8%', '162K', '-0.2%', '$4.5B') to raw float."""
        if raw is None:
            return None
        s = str(raw).strip().replace(",", "").replace("$", "").replace("€", "").replace("£", "")
        if not s or s in ("-", "N/A", "n/a", "None", "null"):
            return None

        mult = 1.0
        upper = s.upper()
        if upper.endswith("%"):
            s = s[:-1]
        elif upper.endswith("T"):
            mult = 1e12
            s = s[:-1]
        elif upper.endswith("B"):
            mult = 1e9
            s = s[:-1]
        elif upper.endswith("M"):
            mult = 1e6
            s = s[:-1]
        elif upper.endswith("K"):
            mult = 1e3
            s = s[:-1]

        m = re.search(r"[-+]?\d*\.?\d+", s)
        if not m:
            return None
        try:
            return float(m.group(0)) * mult
        except ValueError:
            return None

    @classmethod
    def get_indicator_polarity(cls, title: str, currency: str = "USD") -> str:
        """
        Determines how a higher-than-expected Actual reading affects XAU/USD:
        - 'HIGHER_BULLISH_GOLD': higher actual weakens USD -> Gold UP (e.g., Jobless Claims, Unemployment)
        - 'HIGHER_BEARISH_GOLD': higher actual strengthens USD/Yields -> Gold DOWN (e.g., CPI, NFP, PCE, GDP)
        - 'NEUTRAL': speeches or ambiguous indicators
        """
        t = (title or "").lower()
        curr = (currency or "USD").upper()

        # Non-numeric events
        if any(k in t for k in ("speaks", "speech", "press conference", "minutes", "statement", "holiday", "auction")):
            return "NEUTRAL"

        is_inverse = any(k in t for k in cls.INVERSE_USD_KEYWORDS)
        is_pro = any(k in t for k in cls.PRO_USD_KEYWORDS)

        if curr == "USD":
            if is_inverse:
                return "HIGHER_BULLISH_GOLD"
            if is_pro:
                return "HIGHER_BEARISH_GOLD"
            return "HIGHER_BEARISH_GOLD"  # Default strong US data = stronger USD = bearish gold

        # Major DXY counter-currencies (EUR 57.6%, JPY 13.6%, GBP 11.9%, CAD, CHF):
        # Stronger EUR/GBP/JPY data weakens DXY slightly -> mildly Bullish Gold
        if curr in ("EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY"):
            if is_inverse:
                return "HIGHER_BEARISH_GOLD"
            return "HIGHER_BULLISH_GOLD"

        return "NEUTRAL"

    @classmethod
    def evaluate_economic_event_impact(cls, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares Actual vs Forecast vs Previous numerically with accurate USD/Gold polarity.
        Returns gold_impact, gold_score (-1..+1), surprise_pct, and human-readable Indonesian comparison_note.
        """
        title = str(event.get("event_title") or "Economic Event")
        currency = str(event.get("currency") or "USD").upper()
        impact_lvl = str(event.get("impact_level") or "LOW").upper()

        act_raw = event.get("actual_value")
        fc_raw = event.get("forecast_value")
        prev_raw = event.get("previous_value")

        act = cls.parse_numeric_value(act_raw)
        fc = cls.parse_numeric_value(fc_raw)
        prev = cls.parse_numeric_value(prev_raw)

        polarity = cls.get_indicator_polarity(title, currency)
        impact_w = 1.0 if impact_lvl == "HIGH" else (0.55 if impact_lvl == "MEDIUM" else 0.20)
        curr_w = 1.0 if currency == "USD" else 0.35

        # Case 1: Event already released (Actual available!)
        if act is not None:
            ref = fc if fc is not None else prev
            ref_label = "Forecast" if fc is not None else "Previous"
            ref_raw = fc_raw if fc is not None else prev_raw

            if ref is not None and polarity != "NEUTRAL":
                delta = act - ref
                scale = max(abs(ref), abs(act), 0.2)
                rel_dev = delta / scale  # relative surprise

                # Small noise band (< 1.5% relative deviation and abs < 0.05) = In-Line / Priced-In
                if abs(delta) < 1e-6 or (abs(rel_dev) < 0.015 and abs(delta) < 0.06):
                    return {
                        "is_released": True,
                        "polarity": polarity,
                        "surprise_direction": "IN_LINE",
                        "gold_impact": "NEUTRAL",
                        "gold_score": 0.0,
                        "comparison_note": (
                            f"Sesuai konsensus ({currency}): Actual {act_raw} ≈ {ref_label} {ref_raw} "
                            f"(dampak sudah priced-in → netral/whipsaw)"
                        ),
                    }

                cmp_sign = ">" if delta > 0 else "<"

                # Non-USD Inflation (e.g., GBP/EUR/JPY CPI/PPI) creates a 2-channel tug-of-war on XAU/USD:
                # 1) Hawkish BoE/ECB strengthens GBP/EUR (mildly softens DXY)
                # 2) Global inflation heats up global bond yields (headwind for Gold)
                # Therefore it is NEVER a "Strong Bullish Gold (Weak USD)" trigger — it is secondary/mixed!
                is_inflation_metric = any(k in title.lower() for k in ("cpi", "pce", "ppi", "inflation", "price index"))
                if currency != "USD" and is_inflation_metric:
                    bank_map = {"GBP": "BoE", "EUR": "ECB", "JPY": "BoJ", "AUD": "RBA", "CAD": "BoC", "CHF": "SNB", "CNY": "PBoC"}
                    bank = bank_map.get(currency, f"Bank Sentral {currency}")
                    if delta > 0:
                        note = (
                            f"Data {currency} ({bank}): Actual {act_raw} > {ref_label} {ref_raw} → {currency} menguat "
                            f"(sedikit tekan DXY), namun yield obligasi global ikut naik → dampak ke XAU campuran/sekunder"
                        )
                    else:
                        note = (
                            f"Data {currency} ({bank}): Actual {act_raw} < {ref_label} {ref_raw} → ekspektasi {bank} melunak "
                            f"({currency} melemah vs USD, yield global melandai) → dampak ke XAU campuran/sekunder"
                        )
                    return {
                        "is_released": True,
                        "polarity": "SECONDARY_MIXED",
                        "surprise_direction": "ABOVE" if delta > 0 else "BELOW",
                        "gold_impact": "NEUTRAL",
                        "gold_score": 0.0,
                        "comparison_note": note,
                    }

                higher_is_bullish = polarity == "HIGHER_BULLISH_GOLD"
                raw_gold_dir = 1.0 if (delta > 0) == higher_is_bullish else -1.0
                # Strength scales smoothly from 0.40 (mild surprise) up to 0.95 (major surprise)
                strength = min(0.95, 0.42 + min(abs(rel_dev), 0.35) * 1.5)
                gold_score = round(raw_gold_dir * strength * impact_w * curr_w, 3)

                # Only direct USD releases can qualify as STRONG triggers for XAU/USD
                is_strong = (currency == "USD") and (abs(rel_dev) >= 0.08 or (impact_lvl == "HIGH" and abs(rel_dev) >= 0.04))
                if raw_gold_dir > 0:
                    gold_impact = "STRONG_BULLISH_GOLD" if is_strong else "BULLISH_GOLD"
                    eff_str = (
                        "USD melemah → Bullish XAU"
                        if currency == "USD"
                        else f"Dampak sekunder: {currency} menguat (tekanan ringan DXY) → Bullish ringan XAU"
                    )
                else:
                    gold_impact = "STRONG_BEARISH_GOLD" if is_strong else "BEARISH_GOLD"
                    eff_str = (
                        "USD & Yield menguat → Bearish XAU"
                        if currency == "USD"
                        else f"Dampak sekunder: {currency} melemah (DXY menguat ringan) → Bearish ringan XAU"
                    )

                return {
                    "is_released": True,
                    "polarity": polarity,
                    "surprise_direction": "ABOVE" if delta > 0 else "BELOW",
                    "gold_impact": gold_impact,
                    "gold_score": gold_score,
                    "comparison_note": f"Actual {act_raw} {cmp_sign} {ref_label} {ref_raw} → {eff_str}",
                }

            return {
                "is_released": True,
                "polarity": polarity,
                "surprise_direction": "RELEASED",
                "gold_impact": "NEUTRAL",
                "gold_score": 0.0,
                "comparison_note": f"Actual dirilis di {act_raw} (tanpa angka konsensus pembanding)",
            }

        # Case 2: Upcoming event — compare Forecast vs Previous to read market expectation!
        if fc is not None and prev is not None and polarity != "NEUTRAL":
            exp_delta = fc - prev
            scale = max(abs(prev), abs(fc), 0.2)
            rel_exp = exp_delta / scale
            if abs(rel_exp) >= 0.03:
                higher_is_bullish = polarity == "HIGHER_BULLISH_GOLD"
                exp_dir = 1.0 if (exp_delta > 0) == higher_is_bullish else -1.0
                # Pre-release expectation carries lighter weight (0.25x) than an actual surprise
                gold_score = round(exp_dir * 0.25 * impact_w * curr_w, 3)
                gold_impact = "BULLISH_GOLD" if exp_dir > 0 else "BEARISH_GOLD"
                cmp_sign = ">" if exp_delta > 0 else "<"
                tendency = "condong Bullish XAU" if exp_dir > 0 else "condong Bearish XAU"
                return {
                    "is_released": False,
                    "polarity": polarity,
                    "surprise_direction": "PENDING",
                    "gold_impact": gold_impact,
                    "gold_score": gold_score,
                    "comparison_note": f"Ekspektasi: Forecast {fc_raw} {cmp_sign} Previous {prev_raw} ({tendency})",
                }

        return {
            "is_released": False,
            "polarity": polarity,
            "surprise_direction": "PENDING",
            "gold_impact": "NEUTRAL",
            "gold_score": 0.0,
            "comparison_note": f"Menunggu rilis (Forecast: {fc_raw or '-'} | Previous: {prev_raw or '-'})",
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. LIVE INTERMARKET ENGINE (DXY, US10Y YIELD, WTI CRUDE OIL)
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    async def _fetch_yahoo_quote(client: httpx.AsyncClient, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetches lightweight 5-day daily chart from Yahoo Finance to get authentic live price & % change."""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
        try:
            r = await client.get(url, timeout=3.5)
            if r.status_code != 200:
                return None
            res = r.json().get("chart", {}).get("result", [])
            if not res:
                return None
            meta = res[0].get("meta", {})
            price = meta.get("regularMarketPrice")
            prev = meta.get("chartPreviousClose") or meta.get("previousClose")

            quotes = res[0].get("indicators", {}).get("quote", [{}])[0]
            closes = [float(c) for c in (quotes.get("close") or []) if c is not None]
            if price is None and closes:
                price = closes[-1]
            if prev is None and len(closes) >= 2:
                prev = closes[-2]
            if price is None:
                return None

            price_f = round(float(price), 3 if ticker == "^TNX" else 2)
            prev_f = float(prev) if prev else price_f
            chg = round(price_f - prev_f, 3 if ticker == "^TNX" else 2)
            chg_pct = round((chg / prev_f) * 100.0, 2) if prev_f != 0 else 0.0
            trend = "UP" if chg_pct >= 0.12 else ("DOWN" if chg_pct <= -0.12 else "FLAT")
            return {
                "price": price_f,
                "change": chg,
                "change_pct": chg_pct,
                "trend": trend,
            }
        except Exception as e:
            logger.debug(f"[Intermarket] Yahoo fetch failed for {ticker}: {e}")
            return None

    @classmethod
    async def fetch_intermarket_snapshot(cls) -> Dict[str, Any]:
        """
        Fetches live DXY (US Dollar Index), US10Y (10Y Treasury Yield), and WTI Crude Oil concurrently.
        Computes authentic market regime and direct intermarket impact score for XAU/USD.
        """
        now_ts = time.time()
        if cls._intermarket_cache and (now_ts - cls._intermarket_cache_ts) < cls._INTERMARKET_TTL:
            return cls._intermarket_cache

        async with httpx.AsyncClient(headers=HEADERS, timeout=4.0) as client:
            dxy_q, us10y_q, wti_q = await asyncio.gather(
                cls._fetch_yahoo_quote(client, "DX-Y.NYB"),
                cls._fetch_yahoo_quote(client, "^TNX"),
                cls._fetch_yahoo_quote(client, "CL=F"),
                return_exceptions=True,
            )

        dxy = dxy_q if isinstance(dxy_q, dict) else None
        us10y = us10y_q if isinstance(us10y_q, dict) else None
        wti = wti_q if isinstance(wti_q, dict) else None

        score = 0.0
        parts: List[str] = []

        # DXY: inverse correlation to Gold (strongest weight 0.50)
        dxy_effect = "NEUTRAL"
        if dxy:
            pct = float(dxy["change_pct"])
            if pct <= -0.15:
                dxy_effect = "BULLISH_GOLD"
                score += min(0.50, abs(pct) * 0.65)
            elif pct >= 0.15:
                dxy_effect = "BEARISH_GOLD"
                score -= min(0.50, abs(pct) * 0.65)
            dxy["gold_effect"] = dxy_effect
            sign = "+" if pct >= 0 else ""
            parts.append(f"DXY {dxy['price']:.2f} ({sign}{pct:.2f}%)")

        # US10Y: inverse correlation to Gold (weight 0.38)
        y_effect = "NEUTRAL"
        if us10y:
            pct = float(us10y["change_pct"])
            if pct <= -0.40:
                y_effect = "BULLISH_GOLD"
                score += min(0.38, abs(pct) * 0.18)
            elif pct >= 0.40:
                y_effect = "BEARISH_GOLD"
                score -= min(0.38, abs(pct) * 0.18)
            us10y["gold_effect"] = y_effect
            sign = "+" if pct >= 0 else ""
            parts.append(f"US10Y {us10y['price']:.2f}% ({sign}{pct:.2f}%)")

        # WTI Oil: sharp geopolitical oil spike (+1.8%+) lifts inflation/safe-haven demand
        wti_effect = "NEUTRAL"
        if wti:
            pct = float(wti["change_pct"])
            if pct >= 1.80:
                wti_effect = "BULLISH_GOLD"
                score += min(0.16, pct * 0.05)
            elif pct <= -2.20:
                wti_effect = "BEARISH_GOLD"
                score -= min(0.12, abs(pct) * 0.04)
            wti["gold_effect"] = wti_effect
            sign = "+" if pct >= 0 else ""
            parts.append(f"WTI ${wti['price']:.2f} ({sign}{pct:.2f}%)")

        score = max(-1.0, min(1.0, round(score, 3)))

        # Synthesize authentic Market Regime label
        if wti and float(wti["change_pct"]) >= 2.2 and score >= 0.10:
            regime = "Risk-Off & Energy Inflation Hedge (Bullish XAU)"
        elif dxy_effect == "BULLISH_GOLD" and y_effect == "BULLISH_GOLD":
            regime = "Weak-Dollar & Cooling Yield Rally (Bullish XAU)"
        elif dxy_effect == "BEARISH_GOLD" and y_effect == "BEARISH_GOLD":
            regime = "Hawkish Dollar & Yield Surge (Bearish XAU)"
        elif score >= 0.22:
            regime = "Intermarket Supportive (Condong Bullish XAU)"
        elif score <= -0.22:
            regime = "Intermarket Headwind (Condong Bearish XAU)"
        else:
            regime = "Mixed Intermarket / Transisi Sesi (Netral)"

        evidence = " • ".join(parts) if parts else "Menunggu pembaruan quote DXY, US10Y & WTI live."

        snapshot = {
            "dxy": dxy,
            "us10y": us10y,
            "wti": wti,
            "intermarket_score": score,
            "market_regime": regime,
            "market_regime_evidence": evidence,
            "updated_at_wib": datetime.now(WIB).strftime("%H:%M WIB"),
        }

        if dxy or us10y or wti:
            cls._intermarket_cache = snapshot
            cls._intermarket_cache_ts = now_ts
        return snapshot

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. HISTORICAL MARKET REACTION TRACKER (CANDLE IMPACT ON PAST RELEASES)
    # ═══════════════════════════════════════════════════════════════════════════

    @classmethod
    async def fetch_recent_released_usd_events(cls, days_back: int = 14) -> List[Dict[str, Any]]:
        """
        Fetches recently released HIGH/MEDIUM USD economic events (with actual & forecast)
        directly from TradingView Calendar API so historical market reactions work even on cold serverless DBs.
        """
        now_ts = time.time()
        if cls._recent_tv_usd_cache and (now_ts - cls._recent_tv_usd_ts) < 300.0:
            return cls._recent_tv_usd_cache

        now = datetime.now(timezone.utc)
        from_date = (now - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00.000Z")
        to_date = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        tv_url = f"https://economic-calendar.tradingview.com/events?from={from_date}&to={to_date}&countries=US"
        tv_headers = {
            "User-Agent": HEADERS["User-Agent"],
            "Origin": "https://www.tradingview.com",
            "Referer": "https://www.tradingview.com/",
        }
        try:
            async with httpx.AsyncClient(headers=tv_headers, timeout=4.5) as client:
                r = await client.get(tv_url)
                if r.status_code == 200:
                    raw = r.json().get("result", [])
                    out: List[Dict[str, Any]] = []
                    for ev in raw:
                        imp_num = int(ev.get("importance") or 0)
                        if imp_num < 0:
                            continue
                        act = ev.get("actual")
                        fc = ev.get("forecast")
                        if act is None or fc is None:
                            continue
                        unit = str(ev.get("unit") or "").strip()
                        scale = str(ev.get("scale") or "").strip()
                        suffix = unit if unit in ("%", "K", "M", "B") else (scale if scale in ("K", "M", "B") else "")

                        def fmt(v: Any) -> str:
                            if v is None:
                                return "-"
                            try:
                                fv = float(v)
                                s = f"{int(fv)}" if fv.is_integer() else f"{fv:.2f}".rstrip("0").rstrip(".")
                                return f"{s}{suffix}"
                            except Exception:
                                return str(v)

                        out.append({
                            "currency": "USD",
                            "event_title": str(ev.get("title") or "US Economic Data"),
                            "impact_level": "HIGH" if imp_num >= 1 else "MEDIUM",
                            "scheduled_at": str(ev.get("date") or ""),
                            "actual_value": fmt(act),
                            "forecast_value": fmt(fc),
                            "previous_value": fmt(ev.get("previous")),
                        })
                    if out:
                        cls._recent_tv_usd_cache = out
                        cls._recent_tv_usd_ts = now_ts
                        return out
        except Exception as e:
            logger.debug(f"[MacroIntelligence] TradingView past US events fetch failed: {e}")
        return cls._recent_tv_usd_cache or []

    @classmethod
    def analyze_historical_news_reactions(
        cls,
        economic_events: List[Dict[str, Any]],
        h1_candles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Cross-references recently released HIGH/MEDIUM USD events against authentic 1H XAU/USD candles
        to measure exact 1-hour pip movement, volatility range (whipsaw), and theoretical alignment.
        """
        if not h1_candles:
            return {
                "recent_reactions": [],
                "avg_release_range_pips": 0.0,
                "avg_top_impulse_pips": 0.0,
                "summary": "Data historis candle belum tersedia untuk mengukur reaksi rilis.",
            }

        # Normalize candle timestamps to UTC epoch hours
        candle_list: List[Tuple[datetime, Dict[str, Any]]] = []
        for c in h1_candles:
            ts = c.get("timestamp")
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    continue
            if not isinstance(ts, datetime):
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            candle_list.append((ts.astimezone(timezone.utc), c))
        candle_list.sort(key=lambda x: x[0])

        # Compute authentic 30-day top-10% high-volatility 1H impulse benchmark from real candles
        ranges_pips = sorted(
            [round((float(c["high"]) - float(c["low"])) * 10.0, 1) for _, c in candle_list if float(c["high"]) > float(c["low"])],
            reverse=True,
        )
        top_n = max(1, len(ranges_pips) // 10)
        avg_top_impulse = round(sum(ranges_pips[:top_n]) / top_n, 1) if ranges_pips else 160.0

        now_utc = datetime.now(timezone.utc)
        reactions: List[Dict[str, Any]] = []

        for ev in economic_events or []:
            curr = str(ev.get("currency") or "").upper()
            imp = str(ev.get("impact_level") or "LOW").upper()
            if curr != "USD" or imp not in ("HIGH", "MEDIUM"):
                continue

            eval_res = cls.evaluate_economic_event_impact(ev)
            if not eval_res["is_released"]:
                continue

            sched = ev.get("scheduled_at")
            if isinstance(sched, str):
                try:
                    sched = datetime.fromisoformat(sched.replace("Z", "+00:00"))
                except Exception:
                    continue
            if not isinstance(sched, datetime):
                continue
            if sched.tzinfo is None:
                sched = sched.replace(tzinfo=timezone.utc)
            sched_utc = sched.astimezone(timezone.utc)

            # Must be at least 30 minutes in the past so the reaction candle exists
            if sched_utc > now_utc - timedelta(minutes=30):
                continue

            # Find the 1H candle containing or immediately following sched_utc (within 90 minutes)
            best_idx = None
            best_diff = 5400.0  # 90 min
            for idx, (c_ts, _) in enumerate(candle_list):
                diff = abs((c_ts - sched_utc).total_seconds())
                if diff <= best_diff:
                    best_diff = diff
                    best_idx = idx

            if best_idx is None:
                continue

            c0 = candle_list[best_idx][1]
            c1 = candle_list[best_idx + 1][1] if (best_idx + 1) < len(candle_list) else c0

            open_p = float(c0["open"])
            close_1h = float(c1["close"]) if best_idx + 1 < len(candle_list) else float(c0["close"])
            hi = max(float(c0["high"]), float(c1["high"]))
            lo = min(float(c0["low"]), float(c1["low"]))

            move_pips = round((close_1h - open_p) * 10.0, 1)
            range_pips = round((hi - lo) * 10.0, 1)

            if move_pips >= 25.0:
                actual_dir = "BULLISH"
            elif move_pips <= -25.0:
                actual_dir = "BEARISH"
            else:
                actual_dir = "WHIPSAW"

            expected_imp = eval_res["gold_impact"]
            if expected_imp == "NEUTRAL":
                verdict = "Sesuai Konsensus (Whipsaw)"
            elif ("BULLISH" in expected_imp and actual_dir == "BULLISH") or ("BEARISH" in expected_imp and actual_dir == "BEARISH"):
                verdict = "Sesuai Teori Fundamental"
            elif actual_dir == "WHIPSAW":
                verdict = "Reaksi Tertahan / Priced-In"
            else:
                verdict = "Divergensi (Sell/Buy the Fact)"

            reactions.append({
                "event_title": str(ev.get("event_title") or "USD Data"),
                "impact_level": imp,
                "released_at_wib": sched_utc.astimezone(WIB).strftime("%d %b, %H:%M WIB"),
                "actual": str(ev.get("actual_value") or "-"),
                "forecast": str(ev.get("forecast_value") or "-"),
                "previous": str(ev.get("previous_value") or "-"),
                "gold_impact": expected_imp,
                "move_1h_pips": move_pips,
                "range_1h_pips": range_pips,
                "direction": actual_dir,
                "verdict": verdict,
            })

        # Keep most recent 4 matched reactions (prioritizing HIGH impact)
        reactions.sort(key=lambda r: (r["impact_level"] == "HIGH", r["range_1h_pips"]), reverse=True)
        top_reactions = reactions[:4]

        avg_rel_range = (
            round(sum(r["range_1h_pips"] for r in top_reactions) / len(top_reactions), 1)
            if top_reactions
            else avg_top_impulse
        )

        if top_reactions:
            lead = top_reactions[0]
            sign = "+" if lead["move_1h_pips"] >= 0 else ""
            summary = (
                f"Rekam jejak {len(top_reactions)} rilis USD terbaru: rata-rata rentang volatilitas 1 jam "
                f"±{avg_rel_range:.0f} pips. Contoh terbaru '{lead['event_title']}' (Act {lead['actual']} vs Fc {lead['forecast']}) "
                f"menggerakkan XAU {sign}{lead['move_1h_pips']:.0f} pips (range {lead['range_1h_pips']:.0f}p — {lead['verdict']})."
            )
        else:
            summary = (
                f"Benchmark volatilitas historis 30 hari XAU/USD pada jam rilis impulsif (top 10% candle 1H): "
                f"rata-rata rentang gerak ±{avg_top_impulse:.0f} pips per jam — wajib disiplin News Guard & SL ketat."
            )

        return {
            "recent_reactions": top_reactions,
            "avg_release_range_pips": avg_rel_range,
            "avg_top_impulse_pips": avg_top_impulse,
            "summary": summary,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # 4. TIME-DECAYED, THEME-CLASSIFIED, NEGATION-AWARE GEOPOLITICAL & NEWS AI
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def classify_news_sentiment_smart(text: str) -> Tuple[str, float, str]:
        """
        Context-aware financial & geopolitical sentiment scorer for Gold (XAU/USD).
        Detects primary theme and handles contrast clauses ('falls despite tensions').
        Returns (sentiment_label, score -0.95..+0.95, theme_tag).
        """
        lower = (text or "").lower()

        # 1. Detect primary theme
        if any(k in lower for k in ("war", "conflict", "iran", "israel", "middle east", "hormuz", "ukraine", "russia", "missile", "strike", "attack", "tariff", "sanction", "trade war", "geopolitic", "ceasefire", "truce", "peace deal")):
            theme = "GEOPOLITIK"
        elif any(k in lower for k in ("fed", "federal reserve", "powell", "fomc", "rate cut", "rate hike", "central bank", "monetary policy")):
            theme = "THE_FED"
        elif any(k in lower for k in ("cpi", "pce", "ppi", "inflation", "nfp", "payroll", "jobs", "unemployment", "gdp", "recession")):
            theme = "INFLASI_MAKRO"
        elif any(k in lower for k in ("dollar", "dxy", "greenback", "yield", "treasury", "bond")):
            theme = "DOLAR_YIELD"
        else:
            theme = "DEMAND_EMAS"

        # 2. If headline has a contrast conjunction ("despite", "even as", "amid", "after"),
        # the clause BEFORE the contrast expresses the actual market price reaction!
        main_clause = lower
        bg_clause = ""
        for sep in (" despite ", " even as ", " shrugging off ", " notwithstanding "):
            if sep in lower:
                parts = lower.split(sep, 1)
                main_clause, bg_clause = parts[0], parts[1]
                break

        bullish_phrases = (
            ("gold surges", 0.55), ("gold jumps", 0.50), ("gold rallies", 0.50), ("gold climbs", 0.45),
            ("gold rises", 0.42), ("gold gains", 0.40), ("record high", 0.50), ("safe-haven demand", 0.48),
            ("safe haven", 0.40), ("rate cut", 0.42), ("dovish", 0.42), ("fed pivot", 0.45),
            ("dollar falls", 0.42), ("dollar slides", 0.42), ("weak dollar", 0.40), ("yields drop", 0.42),
            ("yields fall", 0.40), ("escalation", 0.45), ("escalates", 0.45), ("airstrike", 0.45),
            ("missile", 0.42), ("retaliation", 0.45), ("tariff", 0.30), ("sanctions", 0.30),
            ("central bank buying", 0.45), ("inflation hedge", 0.35), ("war", 0.32), ("conflict", 0.28),
            ("tensions", 0.28), ("crisis", 0.32), ("surge", 0.28), ("rally", 0.28), ("soar", 0.32),
        )
        bearish_phrases = (
            ("gold falls", 0.55), ("gold drops", 0.55), ("gold plunges", 0.60), ("gold slides", 0.50),
            ("gold tumbles", 0.55), ("gold retreats", 0.48), ("gold dips", 0.40), ("gold slips", 0.40),
            ("gold sell-off", 0.55), ("gold selloff", 0.55), ("rate hike", 0.48), ("hawkish", 0.45),
            ("higher for longer", 0.45), ("dollar surges", 0.45), ("dollar rallies", 0.45), ("strong dollar", 0.42),
            ("yields surge", 0.45), ("yields rise", 0.42), ("yields jump", 0.45), ("ceasefire", 0.48),
            ("truce", 0.45), ("peace deal", 0.50), ("de-escalation", 0.48), ("tensions ease", 0.45),
            ("fears ease", 0.42), ("fades", 0.32), ("eases", 0.28), ("cools", 0.26), ("plunge", 0.35),
            ("slump", 0.35), ("tumble", 0.35), ("retreat", 0.30), ("sell-off", 0.35),
        )

        score = 0.0
        for phrase, w in bullish_phrases:
            if phrase in main_clause:
                score += w
            elif bg_clause and phrase in bg_clause:
                # Background clause after "despite" has minimal weight (0.15x) so it never overrides main price action!
                score += w * 0.15

        for phrase, w in bearish_phrases:
            if phrase in main_clause:
                score -= w
            elif bg_clause and phrase in bg_clause:
                score -= w * 0.15

        score = max(-0.95, min(0.95, round(score, 2)))
        if score >= 0.20:
            label = "POSITIVE"
        elif score <= -0.20:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"
        return label, score, theme

    @classmethod
    def analyze_geopolitical_and_macro_news(
        cls,
        news_articles: List[Dict[str, Any]],
        intermarket: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Aggregates live news articles using exponential recency weighting (Time-Decay),
        theme categorization, and contrast-aware sentiment scoring.
        """
        now_utc = datetime.now(timezone.utc)
        weighted_sum = 0.0
        weight_total = 0.0
        fresh_count = 0
        theme_counts: Dict[str, int] = {}
        bullish_drivers: List[str] = []
        bearish_drivers: List[str] = []

        for art in (news_articles or [])[:25]:
            title = str(art.get("title") or "").strip()
            if not title:
                continue
            # Filter out any legacy non-XAU single-stock headlines that might linger in old DB rows
            t_low = title.lower()
            if not any(k in t_low for k in (
                "gold", "xau", "bullion", "silver", "metal", "fed", "powell", "fomc", "rate",
                "dollar", "dxy", "yield", "treasury", "inflation", "cpi", "pce", "nfp", "payroll",
                "jobs", "gdp", "recession", "war", "conflict", "iran", "israel", "middle east",
                "ukraine", "russia", "tariff", "sanction", "geopolit", "safe-haven", "safe haven", "oil", "crude"
            )):
                continue

            pub = art.get("published_at")
            if isinstance(pub, str):
                try:
                    pub = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                except Exception:
                    pub = now_utc - timedelta(hours=12)
            elif not isinstance(pub, datetime):
                pub = now_utc - timedelta(hours=12)
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)

            age_h = max(0.0, (now_utc - pub.astimezone(timezone.utc)).total_seconds() / 3600.0)
            if age_h <= 3.0:
                decay_w = 1.00
                fresh_count += 1
            elif age_h <= 12.0:
                decay_w = 0.75
            elif age_h <= 24.0:
                decay_w = 0.50
            elif age_h <= 48.0:
                decay_w = 0.25
            else:
                decay_w = 0.12

            lbl, smart_score, theme = cls.classify_news_sentiment_smart(title)
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

            # Geopolitik & The Fed headlines carry slightly stronger gold-catalyst weight
            theme_mult = 1.20 if theme in ("GEOPOLITIK", "THE_FED") else 1.0
            w = decay_w * theme_mult
            weighted_sum += smart_score * w
            weight_total += w

            src = str(art.get("source") or "Wire")
            if smart_score >= 0.25 and len(bullish_drivers) < 2:
                bullish_drivers.append(f"[{theme}] {title} ({src})")
            elif smart_score <= -0.25 and len(bearish_drivers) < 2:
                bearish_drivers.append(f"[{theme}] {title} ({src})")

        geo_score = round(weighted_sum / weight_total, 3) if weight_total > 0 else 0.0

        # Blend WTI oil geopolitical spike mildly if intermarket shows sharp energy shock
        if intermarket and isinstance(intermarket.get("wti"), dict):
            wti_pct = float(intermarket["wti"].get("change_pct") or 0.0)
            if wti_pct >= 2.0:
                geo_score = min(1.0, round(geo_score + 0.14, 3))
            elif wti_pct <= -2.5:
                geo_score = max(-1.0, round(geo_score - 0.10, 3))

        dominant_theme = max(theme_counts.items(), key=lambda x: x[1])[0] if theme_counts else "GEOPOLITIK"

        theme_labels = {
            "GEOPOLITIK": "Ketegangan Geopolitik & Safe-Haven",
            "THE_FED": "Arah Suku Bunga The Fed",
            "INFLASI_MAKRO": "Data Inflasi & Makro AS",
            "DOLAR_YIELD": "Pergerakan Dolar & Yield Obligasi",
            "DEMAND_EMAS": "Permintaan Fisik & Pasar Emas",
        }
        dom_label = theme_labels.get(dominant_theme, dominant_theme)
        bias_txt = "mendukung Emas (Bullish)" if geo_score >= 0.15 else ("menekan Emas (Bearish)" if geo_score <= -0.15 else "cenderung berimbang (Netral)")

        lead_headline = bullish_drivers[0] if (geo_score >= 0 and bullish_drivers) else (
            bearish_drivers[0] if bearish_drivers else (bullish_drivers[0] if bullish_drivers else "")
        )
        summary = (
            f"Narasi dominan ({fresh_count} berita segar <3 jam): {dom_label} {bias_txt}."
            + (f" Sorotan utama: {lead_headline}." if lead_headline else "")
        )

        return {
            "geo_score": geo_score,
            "dominant_theme": dominant_theme,
            "dominant_theme_label": dom_label,
            "fresh_count": fresh_count,
            "bullish_drivers": bullish_drivers,
            "bearish_drivers": bearish_drivers,
            "summary": summary,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # 5. UNIFIED FUNDAMENTAL PILLAR EVALUATOR (ECONOMIC SURPRISES + INTERMARKET)
    # ═══════════════════════════════════════════════════════════════════════════

    @classmethod
    def evaluate_fundamental_pillar(
        cls,
        economic_events: List[Dict[str, Any]],
        intermarket: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Computes authentic Fundamental Pillar score (-1..+1) by combining:
        - Numeric Actual vs Forecast surprises on recently released events (recency-weighted)
        - Forecast vs Previous expectations on upcoming high-impact events
        - Live Intermarket regime (DXY Dollar Index & US10Y Treasury Yield)
        """
        now_utc = datetime.now(timezone.utc)
        ev_weighted_sum = 0.0
        ev_weight_total = 0.0
        notable_comparisons: List[str] = []

        for ev in economic_events or []:
            res = cls.evaluate_economic_event_impact(ev)
            if abs(res["gold_score"]) < 0.01 and not res["is_released"]:
                continue

            sched = ev.get("scheduled_at")
            if isinstance(sched, str):
                try:
                    sched = datetime.fromisoformat(sched.replace("Z", "+00:00"))
                except Exception:
                    sched = now_utc
            elif not isinstance(sched, datetime):
                sched = now_utc
            if sched.tzinfo is None:
                sched = sched.replace(tzinfo=timezone.utc)

            hours_away = abs((now_utc - sched.astimezone(timezone.utc)).total_seconds()) / 3600.0
            if res["is_released"]:
                # Fresh actual releases (< 24h) dominate fundamental momentum
                rec_w = 1.0 if hours_away <= 12 else (0.70 if hours_away <= 36 else 0.30)
            else:
                # Upcoming event forecast expectation carries light anticipatory weight
                rec_w = 0.35 if hours_away <= 24 else 0.15

            ev_weighted_sum += res["gold_score"] * rec_w
            ev_weight_total += rec_w

            if len(notable_comparisons) < 3 and (res["is_released"] or str(ev.get("impact_level", "")).upper() == "HIGH"):
                notable_comparisons.append(f"{ev.get('currency', 'USD')} {ev.get('event_title', '')}: {res['comparison_note']}")

        event_score = (ev_weighted_sum / ev_weight_total) if ev_weight_total > 0 else 0.0
        intermarket_score = float(intermarket.get("intermarket_score", 0.0) or 0.0)

        # Blend: 55% live Intermarket (DXY + US10Y real-time tape) + 45% Calendar Actual/Forecast surprises
        if ev_weight_total > 0:
            fund_score = max(-1.0, min(1.0, round(intermarket_score * 0.55 + event_score * 0.45, 3)))
        else:
            fund_score = max(-1.0, min(1.0, round(intermarket_score, 3)))

        regime = str(intermarket.get("market_regime") or "Transisi Makro")
        evidence = str(intermarket.get("market_regime_evidence") or "")
        comp_txt = (" " + " | ".join(notable_comparisons[:2]) + ".") if notable_comparisons else ""
        summary = f"Rezim Intermarket: {regime} ({evidence}).{comp_txt}"

        return {
            "fund_score": fund_score,
            "event_surprise_score": round(event_score, 3),
            "intermarket_score": intermarket_score,
            "notable_comparisons": notable_comparisons,
            "summary": summary.strip(),
        }
