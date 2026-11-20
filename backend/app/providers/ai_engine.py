import json
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah Senior Institutional XAU/USD Direct Scalping & Quantitative Strategist.
Tugas utamamu: menganalisis data multi-timeframe real-time (M5, M15, H1), ATR volatilitas, struktur swing, sesi pasar aktif, kalender ekonomi, dan sentimen berita untuk menghasilkan SETUP SCALPING SIAP EKSEKUSI (Entry, SL, TP1, TP2, TP3) yang presisi.

ATURAN MUTLAK INTEGRITAS DATA & ZERO-HALLUCINATION:
1. HARGA AKTIF PASAR: Seluruh angka harga (Entry, SL, TP1, TP2, TP3, Support, Resistance) WAJIB berpatokan langsung pada `current_price` di JSON input. JANGAN PERNAH memakai harga lama/halusinasi.
2. HUKUM FISIKA TRADING (WAJIB 100% VALID):
   - BUY: `stop_loss < entry_low <= entry_price <= entry_high < take_profit_1 < take_profit_2 < take_profit_3`
   - SELL: `stop_loss > entry_high >= entry_price >= entry_low > take_profit_1 > take_profit_2 > take_profit_3`
3. STRATEGI DIRECT SCALPING XAU/USD (BERBASIS ATR & STRUKTUR SWING M5/M15):
   - Prioritaskan setup **DIRECT SCALPING** (`BUY` atau `SELL` dengan `execution_type: "INSTANT"` jika harga sudah di area eksekusi atau `"LIMIT"` jika pullback tipis 5–18 pips).
   - JANGAN malas memberikan `WAIT` ketika harga berada di range intraday lebar! Dalam kondisi sideways/range, manfaatkan rejection Support/Resistance M15 atau momentum EMA M5 untuk scalping terarah.
   - Hanya gunakan `WAIT` jika ada rilis berita HIGH-IMPACT USD (NFP/CPI/FOMC/PCE) kurang dari 15 menit lagi.
   - **ZONA ENTRY KETAT**: Lebar maksimal 10–20 pips ($1.00–$2.00) di dekat `current_price` agar langsung bisa dieksekusi scalper.
   - **STOP LOSS (SL) DINAMIS BERBASIS ATR & SWING**:
     * Letakkan di balik swing low/high M5–M15 terdekat + buffer tipis, disesuaikan dengan `atr_14` M15 saat ini (kisaran ideal 25–65 pips / $2.50–$6.50 tergantung sesi Asia vs London/NY Killzone).
     * Jangan terlalu sempit (< 20 pips rentan sweep) dan jangan terlalu lebar (> 75 pips untuk scalping).
   - **3-TIER TAKE PROFIT SCALING (WAJIB LENGKAP TP1, TP2, TP3)**:
     * **TP1 (Quick Scalp — Amankan 40% Lot)**: Target cepat ~0.9x–1.2x jarak SL (25–50 pips) di likuiditas minor terdekat → langsung geser SL ke Breakeven (BEP).
     * **TP2 (Main Intraday Target — Amankan 40% Lot)**: Target struktur utama ~1.8x–2.3x jarak SL (55–100 pips) di area S/R M15/H1 → geser SL ke TP1 (Profit Locked).
     * **TP3 (Extended Runner — Tahan 20% Lot)**: Target ekspansi impuls ~2.8x–3.8x jarak SL (95–170 pips) di zona likuiditas major H1 untuk memaksimalkan trend continuation.
4. BAHASA & RINGKASAN:
   - Gunakan Bahasa Indonesia profesional, lugas, taktis, langsung ke poin eksekusi (maksimal 2–3 kalimat padat per bagian).

OUTPUT HARUS BERUPA JSON VALID MURNI TANPA MARKDOWN WRAPPER:
{
  "bias": "BULLISH" | "BEARISH" | "NEUTRAL",
  "confidence_score": integer (55-95),
  "summary": "Ringkasan bias 2 kalimat yang menyatukan struktur M5/M15/H1, sesi aktif, dan sentimen makro/geopolitik.",
  "fundamental_notes": "Dampak agenda kalender ekonomi terdekat, suku bunga Fed, Yield US10Y & DXY.",
  "geopolitical_notes": "Dampak sentimen berita global & safe-haven terkini ke permintaan emas.",
  "technical_notes": "Analisis sinkronisasi H1 (bias) + M15 (struktur & ATR) + M5 (trigger entry & price action).",
  "key_levels": {
    "support": [number, number],
    "resistance": [number, number]
  },
  "trade_setup": {
    "action": "BUY" | "SELL" | "WAIT",
    "action_label": "BUY NOW (SCALP)" | "BUY LIMIT (PULLBACK)" | "SELL NOW (SCALP)" | "SELL LIMIT (RALLY)" | "WAIT / NEWS GUARD",
    "execution_type": "INSTANT" | "LIMIT" | "WAIT",
    "scalp_timeframe": "M5 / M15",
    "entry_zone": "$3562.50 - $3564.20",
    "entry_price": 3563.50,
    "stop_loss": 3559.70,
    "take_profit_1": 3567.30,
    "take_profit_2": 3571.50,
    "take_profit_3": 3576.50,
    "lot_management": "40% TP1 (SL→BEP) • 40% TP2 (SL→TP1) • 20% Runner TP3",
    "technical_rationale": "Alasan spesifik berbasis struktur M5/M15, EMA/RSI, ATR, dan rencana scaling TP1-TP2-TP3.",
    "invalidation_level": "Close candle M15 di bawah $3559.70 membatalkan setup buy scalp ini."
  },
  "risk_factors": [
    "Faktor risiko 1",
    "Faktor risiko 2"
  ],
  "sources": [
    "Multi-Timeframe Price Action (M5, M15, H1) & ATR(14)",
    "Kalender Ekonomi ForexFactory",
    "Arus Berita Global & Geopolitik XAU/USD"
  ]
}
"""


class AIAgentEngine:
    @staticmethod
    async def synthesize_market_bias(
        symbol: str,
        price_snapshot: Dict[str, Any],
        technical_data: Dict[str, Any],
        economic_events: List[Dict[str, Any]],
        news_articles: List[Dict[str, Any]],
        mtf_technical: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes multi-timeframe scalping + 3-pillar data using:
        1. Anthropic Claude API (Sonnet 4.5 / Haiku 4.5) when valid ANTHROPIC_API_KEY is configured
        2. Gemini API (if configured)
        3. OpenRouter AI Gateway (if configured)
        4. Built-in ATR & Multi-Timeframe Quantitative Direct Scalping Engine
        Always followed by a smart non-destructive physics & pip sanitizer.
        """
        curr_price = float(price_snapshot.get("current_price", 0.0) or technical_data.get("latest_price", 3560.0))
        m15_tech = (mtf_technical or {}).get("15m") or technical_data
        m5_tech = (mtf_technical or {}).get("5m") or m15_tech
        h1_tech = (mtf_technical or {}).get("1h") or technical_data

        payload_data = {
            "symbol": symbol,
            "current_price": curr_price,
            "session": m15_tech.get("session_name", "Global Session"),
            "session_volatility": m15_tech.get("session_volatility", "MEDIUM"),
            "mtf_technical": {
                "m5_execution": {
                    "trend": m5_tech.get("trend_direction"),
                    "rsi_14": m5_tech.get("rsi_14"),
                    "ema_9": m5_tech.get("ema_9"),
                    "ema_21": m5_tech.get("ema_21"),
                    "atr_14": m5_tech.get("atr_14"),
                    "price_action": m5_tech.get("price_action"),
                    "price_action_note": m5_tech.get("price_action_note"),
                },
                "m15_scalp_structure": {
                    "trend": m15_tech.get("trend_direction"),
                    "rsi_14": m15_tech.get("rsi_14"),
                    "ema_9": m15_tech.get("ema_9"),
                    "ema_21": m15_tech.get("ema_21"),
                    "atr_14": m15_tech.get("atr_14"),
                    "atr_pips": m15_tech.get("atr_pips"),
                    "swing_lows": m15_tech.get("swing_lows", []),
                    "swing_highs": m15_tech.get("swing_highs", []),
                    "supports": m15_tech.get("support_levels", []),
                    "resistances": m15_tech.get("resistance_levels", []),
                    "price_action": m15_tech.get("price_action"),
                },
                "h1_macro_bias": {
                    "trend": h1_tech.get("trend_direction"),
                    "rsi_14": h1_tech.get("rsi_14"),
                    "sma_20": h1_tech.get("sma_20"),
                    "sma_50": h1_tech.get("sma_50"),
                    "atr_14": h1_tech.get("atr_14"),
                    "supports": h1_tech.get("support_levels", []),
                    "resistances": h1_tech.get("resistance_levels", []),
                },
            },
            "upcoming_economic_events": economic_events[:4],
            "recent_news_sentiment": news_articles[:4],
        }

        # 1. Try Anthropic Claude API if valid key exists
        if settings.ANTHROPIC_API_KEY and not settings.ANTHROPIC_API_KEY.startswith("your-"):
            try:
                raw_claude = await AIAgentEngine._call_claude_api(payload_data)
                sanitized = AIAgentEngine._sanitize_and_validate_trade_setup(
                    raw_claude,
                    curr_price=curr_price,
                    technical_data=h1_tech,
                    m15_data=m15_tech,
                    m5_data=m5_tech,
                    economic_events=economic_events,
                    news_articles=news_articles,
                )
                logger.info("[AIAgentEngine] Claude scalping analysis synthesized & validated!")
                return sanitized
            except Exception as e:
                logger.warning(f"Claude API failed, falling back: {e}")

        # 2. Try Gemini API if key exists
        if settings.GEMINI_API_KEY:
            try:
                raw_gemini = await AIAgentEngine._call_gemini_api(payload_data)
                sanitized = AIAgentEngine._sanitize_and_validate_trade_setup(
                    raw_gemini,
                    curr_price=curr_price,
                    technical_data=h1_tech,
                    m15_data=m15_tech,
                    m5_data=m5_tech,
                    economic_events=economic_events,
                    news_articles=news_articles,
                )
                logger.info("[AIAgentEngine] Gemini scalping analysis synthesized & validated!")
                return sanitized
            except Exception as e:
                logger.warning(f"Gemini API failed, trying OpenRouter fallback: {e}")

        # 3. Try OpenRouter API if key exists
        if settings.OPENROUTER_API_KEY:
            try:
                raw_openrouter = await AIAgentEngine._call_openrouter_api(payload_data)
                sanitized = AIAgentEngine._sanitize_and_validate_trade_setup(
                    raw_openrouter,
                    curr_price=curr_price,
                    technical_data=h1_tech,
                    m15_data=m15_tech,
                    m5_data=m5_tech,
                    economic_events=economic_events,
                    news_articles=news_articles,
                )
                logger.info("[AIAgentEngine] OpenRouter scalping analysis synthesized & validated!")
                return sanitized
            except Exception as e:
                logger.warning(f"OpenRouter API failed, falling back to quantitative scalping engine: {e}")

        # 4. Built-in Multi-Timeframe ATR Quantitative Direct Scalping Engine (Zero-cost, sub-10ms)
        raw_heuristic = AIAgentEngine._heuristic_synthesis(
            symbol=symbol,
            price_snapshot=price_snapshot,
            technical_data=h1_tech,
            economic_events=economic_events,
            news_articles=news_articles,
            m15_data=m15_tech,
            m5_data=m5_tech,
        )
        return AIAgentEngine._sanitize_and_validate_trade_setup(
            raw_heuristic,
            curr_price=curr_price,
            technical_data=h1_tech,
            m15_data=m15_tech,
            m5_data=m5_tech,
            economic_events=economic_events,
            news_articles=news_articles,
        )

    @staticmethod
    async def _call_claude_api(data: Dict[str, Any]) -> Dict[str, Any]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        # Claude Sonnet 4.5 first for sharp multi-timeframe reasoning, Haiku 4.5 as fast fallback
        models = [
            "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
        ]
        last_error = None
        for model in models:
            body = {
                "model": model,
                "max_tokens": 2048,
                "temperature": 0.2,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Analisis data multi-timeframe XAU/USD berikut dan hasilkan setup DIRECT SCALPING "
                            "(Entry, SL, TP1, TP2, TP3) dalam format JSON valid:\n"
                            f"{json.dumps(data, default=str)}"
                        ),
                    }
                ],
            }
            try:
                async with httpx.AsyncClient(timeout=12.0) as client:
                    resp = await client.post(url, json=body, headers=headers)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        content_text = res_json["content"][0]["text"].strip()
                        s_idx = content_text.find("{")
                        e_idx = content_text.rfind("}")
                        clean_json = content_text[s_idx:e_idx + 1] if (s_idx != -1 and e_idx > s_idx) else content_text
                        parsed = json.loads(clean_json)
                        logger.info(f"[AIAgentEngine] Anthropic {model} scalping analysis synthesized!")
                        return parsed
                    elif resp.status_code == 401:
                        # Don't waste time retrying another model if API key itself is invalid
                        raise RuntimeError(f"Anthropic HTTP 401 invalid API key")
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text[:180]}"
                        logger.warning(f"Claude {model} returned {last_error}")
            except RuntimeError:
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"Claude {model} call error: {e}")

        raise RuntimeError(f"All Claude models failed. Last error: {last_error}")

    @staticmethod
    async def _call_gemini_api(data: Dict[str, Any]) -> Dict[str, Any]:
        models = ["gemini-2.0-flash", "gemini-1.5-flash"]
        last_error = None

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
            body = {
                "contents": [
                    {
                        "parts": [
                            {"text": SYSTEM_PROMPT},
                            {"text": f"Analisis data multi-timeframe XAU/USD berikut dan hasilkan JSON scalping:\n{json.dumps(data, default=str)}"},
                        ]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.2,
                },
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(url, json=body)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        candidates = res_json.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and "text" in parts[0]:
                                content_text = parts[0]["text"].strip()
                                s_idx = content_text.find("{")
                                e_idx = content_text.rfind("}")
                                if s_idx != -1 and e_idx > s_idx:
                                    content_text = content_text[s_idx:e_idx + 1]
                                return json.loads(content_text.strip())
                    else:
                        last_error = f"{model} HTTP {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue

        raise RuntimeError(f"All Gemini models failed: {last_error}")

    @staticmethod
    async def _call_openrouter_api(data: Dict[str, Any]) -> Dict[str, Any]:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://xauusd-radar.app",
            "X-Title": "XAUUSD RADAR - Institutional Scalping Engine",
        }
        free_models = [
            "qwen/qwen3.8-27b:free",
            "google/gemma-4-26b-a4b-it:free",
            "google/gemma-4-31b-it:free",
        ]
        last_error: Any = None
        for model in free_models:
            try:
                body = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": (
                                "Analisis data multi-timeframe XAU/USD berikut dan hasilkan setup DIRECT SCALPING "
                                "(Entry, SL, TP1, TP2, TP3) dalam format JSON valid:\n"
                                f"{json.dumps(data, default=str)}"
                            ),
                        },
                    ],
                    "max_tokens": 2048,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=body, headers=headers)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        content_text = res_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        if not content_text:
                            continue
                        s_idx = content_text.find("{")
                        e_idx = content_text.rfind("}")
                        if s_idx != -1 and e_idx > s_idx:
                            content_text = content_text[s_idx:e_idx + 1]
                        parsed = json.loads(content_text.strip())
                        logger.info(f"[AIAgentEngine] OpenRouter/{model} scalping analysis synthesized!")
                        return parsed
                    elif resp.status_code == 401:
                        raise RuntimeError("OpenRouter HTTP 401 invalid key")
                    else:
                        last_error = f"HTTP {resp.status_code}"
            except RuntimeError:
                raise
            except Exception as e:
                last_error = str(e)

        raise RuntimeError(f"All OpenRouter models failed. Last error: {last_error}")

    @staticmethod
    def _has_imminent_high_impact_event(economic_events: List[Dict[str, Any]], minutes_window: int = 15) -> Optional[str]:
        """Returns event title if a HIGH impact USD news release occurs within minutes_window."""
        now = datetime.now(timezone.utc)
        for ev in economic_events or []:
            if str(ev.get("impact_level", "")).upper() != "HIGH":
                continue
            sched_raw = ev.get("scheduled_at")
            if not sched_raw:
                continue
            try:
                if isinstance(sched_raw, datetime):
                    sched = sched_raw
                else:
                    sched = datetime.fromisoformat(str(sched_raw).replace("Z", "+00:00"))
                if sched.tzinfo is None:
                    sched = sched.replace(tzinfo=timezone.utc)
                diff_min = (sched - now).total_seconds() / 60.0
                if -5.0 <= diff_min <= float(minutes_window):
                    return str(ev.get("event_title", "High-Impact USD News"))
            except Exception:
                continue
        return None

    @staticmethod
    def _heuristic_synthesis(
        symbol: str,
        price_snapshot: Dict[str, Any],
        technical_data: Dict[str, Any],
        economic_events: List[Dict[str, Any]],
        news_articles: List[Dict[str, Any]],
        m15_data: Optional[Dict[str, Any]] = None,
        m5_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Quantitative Multi-Timeframe (H1 + M15 + M5) ATR-Calibrated Direct Scalping Synthesizer.
        Combines Macro Fundamental (25%), Geopolitics (20%), H1 Structure (25%), and M15/M5 Execution Momentum (30%).
        """
        curr_price = float(price_snapshot.get("current_price", 0.0) or technical_data.get("latest_price", 3560.0))
        m15 = m15_data or technical_data
        m5 = m5_data or m15

        # 1. Multi-Timeframe Technical Score (-1.0 to +1.0)
        def dir_to_score(d: str) -> float:
            u = str(d or "").upper()
            return 0.85 if u == "BULLISH" else (-0.85 if u == "BEARISH" else 0.0)

        h1_score = dir_to_score(technical_data.get("trend_direction", "SIDEWAYS"))
        m15_score = dir_to_score(m15.get("trend_direction", "SIDEWAYS"))
        m5_score = dir_to_score(m5.get("trend_direction", "SIDEWAYS"))

        # Add Price Action micro-trigger nudge on M5/M15
        pa = str(m5.get("price_action") or m15.get("price_action") or "").upper()
        pa_boost = 0.0
        if pa in ("BULLISH_REJECTION", "BULLISH_ENGULFING", "BULLISH_IMPULSE"):
            pa_boost = 0.30
        elif pa in ("BEARISH_REJECTION", "BEARISH_ENGULFING", "BEARISH_IMPULSE"):
            pa_boost = -0.30

        # Add RSI oversold/overbought scalping mean-reversion edge
        m15_rsi = m15.get("rsi_14")
        rsi_edge = 0.0
        if isinstance(m15_rsi, (int, float)):
            if m15_rsi <= 34:
                rsi_edge = 0.35
            elif m15_rsi >= 66:
                rsi_edge = -0.35
            elif 52 <= m15_rsi < 66:
                rsi_edge = 0.15
            elif 34 < m15_rsi <= 48:
                rsi_edge = -0.15

        tech_score = max(-1.0, min(1.0, (h1_score * 0.40) + (m15_score * 0.35) + (m5_score * 0.25) + pa_boost + rsi_edge))

        # 2. Geopolitical Sentiment Score (-1.0 to 1.0)
        news_scores = [float(n.get("sentiment_score", 0.0) or 0.0) for n in news_articles]
        geo_score = sum(news_scores) / len(news_scores) if news_scores else 0.0

        # 3. Fundamental Score (-1.0 to 1.0)
        fund_score = 0.15
        for event in economic_events:
            impact = str(event.get("sentiment_impact", "") or "").upper()
            if "BULLISH_GOLD" in impact or "BEARISH_USD" in impact:
                fund_score += 0.25
            elif "BEARISH_GOLD" in impact or "BULLISH_USD" in impact:
                fund_score -= 0.25
        fund_score = max(-1.0, min(1.0, fund_score))

        # Weighted Composite Score
        composite_score = (tech_score * 0.55) + (fund_score * 0.25) + (geo_score * 0.20)

        # Range Edge Proximity Bonus (for direct scalping even in sideways markets)
        supports = m15.get("support_levels") or technical_data.get("support_levels") or [round(curr_price - 8.0, 2)]
        resistances = m15.get("resistance_levels") or technical_data.get("resistance_levels") or [round(curr_price + 8.0, 2)]
        nearest_sup = max([s for s in supports if s < curr_price], default=round(curr_price - 8.0, 2))
        nearest_res = min([r for r in resistances if r > curr_price], default=round(curr_price + 8.0, 2))
        dist_sup = curr_price - nearest_sup
        dist_res = nearest_res - curr_price

        # If price is tightly hugging Support or Resistance, tilt scalping direction cleanly
        if abs(composite_score) < 0.18:
            if dist_sup < dist_res * 0.65 and dist_sup <= 8.0:
                composite_score += 0.24  # Bounce scalp off Support
            elif dist_res < dist_sup * 0.65 and dist_res <= 8.0:
                composite_score -= 0.24  # Rejection scalp off Resistance

        session_name = m15.get("session_name", "Global Session")

        if composite_score >= 0.12:
            bias = "BULLISH"
            confidence = int(64 + min(30, abs(composite_score) * 32))
            summary = (
                f"Struktur {symbol} pada {session_name} mengonfirmasi peluang BUY Scalp "
                f"dengan dukungan momentum M5/M15 dan reaksi demand di atas Support ${nearest_sup:.2f}."
            )
        elif composite_score <= -0.12:
            bias = "BEARISH"
            confidence = int(64 + min(30, abs(composite_score) * 32))
            summary = (
                f"Struktur {symbol} pada {session_name} mengonfirmasi peluang SELL Scalp "
                f"akibat tekanan supply di bawah Resistance ${nearest_res:.2f} dan momentum bearish M5/M15."
            )
        else:
            # Break tie cleanly using M5 momentum or range proximity so scalpers get an actionable bias
            bias = "BULLISH" if (dist_sup <= dist_res) else "BEARISH"
            confidence = 60
            summary = (
                f"Pasar {symbol} berkonsolidasi dalam range ${nearest_sup:.2f}–${nearest_res:.2f} ({session_name}); "
                f"setup scalping taktis diarahkan mengikuti sisi {bias} terdekat dengan kontrol risiko ketat."
            )

        confidence = max(55, min(94, confidence))

        trade_setup = AIAgentEngine._generate_trade_setup(
            symbol=symbol,
            curr_price=curr_price,
            bias=bias,
            supports=supports,
            resistances=resistances,
            technical_data=technical_data,
            m15_data=m15,
            m5_data=m5,
            economic_events=economic_events,
            news_articles=news_articles,
        )

        sources = [
            f"Multi-Timeframe Price Action M5/M15/H1 & ATR(14) {m15.get('atr_pips', 35.0)} pips",
            f"Sesi Pasar Aktif: {session_name}",
        ]
        if economic_events:
            sources.append(f"Kalender Ekonomi: {economic_events[0].get('event_title', 'Agenda Makro')}")
        if news_articles:
            sources.append(f"Berita Global: {news_articles[0].get('title', 'Headline')[:55]}")

        risks = [
            "Lonjakan spread & whipsaw saat rilis data ekonomi High-Impact AS (NFP/CPI/PCE/FOMC).",
            f"Penembusan candle M15 melewati batas invalidasi ${trade_setup['stop_loss']:.2f} membatalkan setup.",
        ]

        return {
            "bias": bias,
            "confidence_score": confidence,
            "summary": summary,
            "fundamental_notes": (
                "Ekspektasi kebijakan suku bunga The Fed, imbal hasil Treasury AS, serta agenda kalender "
                "ekonomi terdekat membentuk sentimen dasar XAU/USD."
            ),
            "geopolitical_notes": (
                "Dinamika geopolitik global dan aliran aset safe-haven tetap menjadi penopang volatilitas intraday emas."
            ),
            "technical_notes": (
                f"H1: {technical_data.get('trend_direction', 'SIDEWAYS')} | "
                f"M15: {m15.get('trend_direction', 'SIDEWAYS')} (ATR {m15.get('atr_pips', 35.0)} pips, RSI {m15.get('rsi_14', '-')}) | "
                f"M5: {m5.get('price_action_note', m5.get('trend_direction', 'ACTIVE'))}."
            ),
            "key_levels": {
                "support": supports[:2],
                "resistance": resistances[:2],
            },
            "trade_setup": trade_setup,
            "risk_factors": risks,
            "sources": sources,
        }

    @staticmethod
    def _generate_trade_setup(
        symbol: str,
        curr_price: float,
        bias: str,
        supports: List[float],
        resistances: List[float],
        technical_data: Dict[str, Any],
        m15_data: Optional[Dict[str, Any]] = None,
        m5_data: Optional[Dict[str, Any]] = None,
        economic_events: Optional[List[Dict[str, Any]]] = None,
        news_articles: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        ATR-Calibrated Institutional Direct Scalping Engine (SL + TP1 + TP2 + TP3).
        Automatically scales SL and 3-tier TP targets to M15 ATR(14) and nearest fractal swing structure.
        """
        m15 = m15_data or technical_data
        m5 = m5_data or m15
        atr_m15 = float(m15.get("atr_14") or technical_data.get("atr_14") or 3.50)
        session_name = str(m15.get("session_name") or "Global Session")
        session_vol = str(m15.get("session_volatility") or "MEDIUM")

        # Dynamic SL distance calibrated to live M15 ATR (strictly 25 to 65 pips / $2.50 to $6.50)
        vol_mult = 1.35 if session_vol == "HIGH" else (1.20 if session_vol == "MEDIUM_HIGH" else 1.05)
        base_risk = round(max(2.50, min(6.50, atr_m15 * vol_mult)), 2)

        # Check for imminent high-impact news blackout (< 15 min)
        imminent_event = AIAgentEngine._has_imminent_high_impact_event(economic_events or [], minutes_window=15)
        if imminent_event:
            valid_sups = sorted([s for s in supports if s < curr_price], reverse=True)
            valid_res = sorted([r for r in resistances if r > curr_price])
            p_sup = valid_sups[0] if valid_sups else round(curr_price - base_risk, 2)
            p_res = valid_res[0] if valid_res else round(curr_price + base_risk, 2)
            sl = round(curr_price - base_risk, 2)
            tp1 = round(curr_price + base_risk * 1.1, 2)
            tp2 = round(curr_price + base_risk * 2.1, 2)
            tp3 = round(curr_price + base_risk * 3.2, 2)
            return {
                "action": "WAIT",
                "action_label": "WAIT / NEWS GUARD (<15m)",
                "execution_type": "WAIT",
                "scalp_timeframe": "M5 / M15",
                "session_name": session_name,
                "atr_pips": round(atr_m15 * 10.0, 1),
                "entry_zone": f"Tunggu rilis {imminent_event} selesai",
                "entry_price": round(curr_price, 2),
                "stop_loss": sl,
                "take_profit_1": tp1,
                "take_profit_2": tp2,
                "take_profit_3": tp3,
                "risk_reward_ratio": "1 : 3.2",
                "risk_pips": round(base_risk * 10.0, 1),
                "reward_tp1_pips": round((tp1 - curr_price) * 10.0, 1),
                "reward_tp2_pips": round((tp2 - curr_price) * 10.0, 1),
                "reward_tp3_pips": round((tp3 - curr_price) * 10.0, 1),
                "lot_management": "Tahan entry sementara hingga lonjakan spread news mereda",
                "technical_rationale": (
                    f"Perlindungan News Guard aktif: rilis High-Impact '{imminent_event}' berlangsung dalam <15 menit. "
                    f"Hindari whipsaw spread; pantau breakout valid di atas ${p_res:.2f} atau breakdown di bawah ${p_sup:.2f}."
                ),
                "invalidation_level": "Lonjakan spread ekstrem menjelang rilis data High-Impact.",
                "status": "ACTIVE",
                "status_message": f"News Guard Aktif — Tunggu rilis {imminent_event}",
            }

        swing_lows = sorted([float(x) for x in (m15.get("swing_lows") or supports) if float(x) < curr_price], reverse=True)
        swing_highs = sorted([float(x) for x in (m15.get("swing_highs") or resistances) if float(x) > curr_price])
        ema9_m5 = m5.get("ema_9")

        # Pocket half-width scales with ATR: tightly $0.60 - $1.00 (12 - 20 pips full zone)
        half_zone = round(max(0.60, min(1.00, atr_m15 * 0.22)), 2)

        if bias == "BULLISH":
            action = "BUY"
            # Direct Instant Scalp if all 3 timeframes align, or price is near EMA 9 / Support / bullish PA
            all_3tf_bull = (
                str(technical_data.get("trend_direction", "")).upper() == "BULLISH"
                and str(m15.get("trend_direction", "")).upper() == "BULLISH"
                and str(m5.get("trend_direction", "")).upper() == "BULLISH"
            )
            near_ema = ema9_m5 is not None and abs(curr_price - float(ema9_m5)) <= (atr_m15 * 0.65)
            near_sup = bool(swing_lows) and (curr_price - swing_lows[0]) <= (atr_m15 * 1.1)
            is_instant = all_3tf_bull or near_ema or near_sup or str(m5.get("price_action", "")).startswith("BULLISH")

            if is_instant:
                execution_type = "INSTANT"
                action_label = "BUY NOW (SCALP)"
                entry_price = round(curr_price, 2)
            else:
                execution_type = "LIMIT"
                action_label = "BUY LIMIT (PULLBACK)"
                entry_price = round(curr_price - min(1.20, atr_m15 * 0.30), 2)

            entry_low = round(entry_price - half_zone, 2)
            entry_high = round(entry_price + half_zone, 2)
            entry_zone = f"${entry_low:.2f} - ${entry_high:.2f}"

            # Place SL structurally behind nearest M15 swing low if within reasonable ATR risk band
            structural_sl = None
            for sw in swing_lows:
                candidate_sl = round(sw - 0.80, 2)
                dist = entry_price - candidate_sl
                if 2.50 <= dist <= 6.80 and candidate_sl < entry_low:
                    structural_sl = candidate_sl
                    break
            stop_loss = structural_sl if structural_sl is not None else round(entry_price - base_risk, 2)
            risk = round(entry_price - stop_loss, 2)

            # 3-Tier Scalping Targets: TP1 (~1.0x), TP2 (~2.0x), TP3 (~3.2x)
            tp1 = round(entry_price + max(2.50, risk * 1.00), 2)
            tp2 = round(entry_price + max(5.20, risk * 2.00), 2)
            tp3 = round(entry_price + max(8.50, risk * 3.20), 2)

            # Snap TP2/TP3 slightly before major resistance if cleanly aligned
            if swing_highs:
                r1 = swing_highs[0]
                if (tp1 + 1.50) <= (r1 - 0.40) <= (entry_price + risk * 2.50):
                    tp2 = round(r1 - 0.40, 2)
                    tp3 = max(tp3, round(tp2 + risk * 1.15, 2))

            reward1 = round(tp1 - entry_price, 2)
            reward2 = round(tp2 - entry_price, 2)
            reward3 = round(tp3 - entry_price, 2)
            rrr = f"1 : {round(reward3 / risk, 1)}" if risk > 0 else "1 : 3.2"

            pa_text = m5.get("price_action_note") or "momentum buyer M5/M15 terkonfirmasi"
            rationale = (
                f"Direct BUY Scalp ({session_name}, ATR M15 {round(atr_m15 * 10, 1)} pips): {pa_text}. "
                f"Entry di {entry_zone} dengan SL struktural ${stop_loss:.2f} (-{round(risk * 10):.0f} pips). "
                f"Scaling 3-tahap: Kunci 40% di TP1 ${tp1:.2f} (+{round(reward1 * 10):.0f} pips) & geser SL→BEP; "
                f"kunci 40% di TP2 ${tp2:.2f} (+{round(reward2 * 10):.0f} pips) & geser SL→TP1; "
                f"biarkan 20% runner menuju TP3 ${tp3:.2f} (+{round(reward3 * 10):.0f} pips)."
            )
            invalidation = f"Close candle M15 di bawah ${stop_loss:.2f} membatalkan setup BUY scalp."

        else:
            action = "SELL"
            all_3tf_bear = (
                str(technical_data.get("trend_direction", "")).upper() == "BEARISH"
                and str(m15.get("trend_direction", "")).upper() == "BEARISH"
                and str(m5.get("trend_direction", "")).upper() == "BEARISH"
            )
            near_ema = ema9_m5 is not None and abs(curr_price - float(ema9_m5)) <= (atr_m15 * 0.65)
            near_res = bool(swing_highs) and (swing_highs[0] - curr_price) <= (atr_m15 * 1.1)
            is_instant = all_3tf_bear or near_ema or near_res or str(m5.get("price_action", "")).startswith("BEARISH")

            if is_instant:
                execution_type = "INSTANT"
                action_label = "SELL NOW (SCALP)"
                entry_price = round(curr_price, 2)
            else:
                execution_type = "LIMIT"
                action_label = "SELL LIMIT (RALLY)"
                entry_price = round(curr_price + min(1.20, atr_m15 * 0.30), 2)

            entry_low = round(entry_price - half_zone, 2)
            entry_high = round(entry_price + half_zone, 2)
            entry_zone = f"${entry_low:.2f} - ${entry_high:.2f}"

            structural_sl = None
            for sw in swing_highs:
                candidate_sl = round(sw + 0.80, 2)
                dist = candidate_sl - entry_price
                if 2.50 <= dist <= 6.80 and candidate_sl > entry_high:
                    structural_sl = candidate_sl
                    break
            stop_loss = structural_sl if structural_sl is not None else round(entry_price + base_risk, 2)
            risk = round(stop_loss - entry_price, 2)

            tp1 = round(entry_price - max(2.50, risk * 1.00), 2)
            tp2 = round(entry_price - max(5.20, risk * 2.00), 2)
            tp3 = round(entry_price - max(8.50, risk * 3.20), 2)

            if swing_lows:
                s1 = swing_lows[0]
                if (entry_price - risk * 2.50) <= (s1 + 0.40) <= (tp1 - 1.50):
                    tp2 = round(s1 + 0.40, 2)
                    tp3 = min(tp3, round(tp2 - risk * 1.15, 2))

            reward1 = round(entry_price - tp1, 2)
            reward2 = round(entry_price - tp2, 2)
            reward3 = round(entry_price - tp3, 2)
            rrr = f"1 : {round(reward3 / risk, 1)}" if risk > 0 else "1 : 3.2"

            pa_text = m5.get("price_action_note") or "tekanan seller M5/M15 terkonfirmasi"
            rationale = (
                f"Direct SELL Scalp ({session_name}, ATR M15 {round(atr_m15 * 10, 1)} pips): {pa_text}. "
                f"Entry di {entry_zone} dengan SL struktural ${stop_loss:.2f} (-{round(risk * 10):.0f} pips). "
                f"Scaling 3-tahap: Kunci 40% di TP1 ${tp1:.2f} (+{round(reward1 * 10):.0f} pips) & geser SL→BEP; "
                f"kunci 40% di TP2 ${tp2:.2f} (+{round(reward2 * 10):.0f} pips) & geser SL→TP1; "
                f"biarkan 20% runner menuju TP3 ${tp3:.2f} (+{round(reward3 * 10):.0f} pips)."
            )
            invalidation = f"Close candle M15 di atas ${stop_loss:.2f} membatalkan setup SELL scalp."

        mode_hint = "Siap Eksekusi Langsung" if execution_type == "INSTANT" else "Tunggu Pullback ke Zona"
        return {
            "action": action,
            "action_label": action_label,
            "execution_type": execution_type,
            "scalp_timeframe": "M5 / M15",
            "session_name": session_name,
            "atr_pips": round(atr_m15 * 10.0, 1),
            "entry_zone": entry_zone,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit_1": tp1,
            "take_profit_2": tp2,
            "take_profit_3": tp3,
            "risk_reward_ratio": rrr,
            "risk_pips": round(risk * 10.0, 1),
            "reward_tp1_pips": round(reward1 * 10.0, 1),
            "reward_tp2_pips": round(reward2 * 10.0, 1),
            "reward_tp3_pips": round(reward3 * 10.0, 1),
            "lot_management": "40% TP1 (SL→BEP) • 40% TP2 (SL→TP1) • 20% Runner TP3",
            "technical_rationale": rationale,
            "invalidation_level": invalidation,
            "status": "ACTIVE",
            "status_message": f"{action_label} • {mode_hint} (Acuan ${entry_price:.2f} | ATR {round(atr_m15 * 10, 1)} pips)",
        }

    @staticmethod
    def _sanitize_and_validate_trade_setup(
        raw_data: Any,
        curr_price: float,
        technical_data: Optional[Dict[str, Any]] = None,
        m15_data: Optional[Dict[str, Any]] = None,
        m5_data: Optional[Dict[str, Any]] = None,
        economic_events: Optional[List[Dict[str, Any]]] = None,
        news_articles: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Smart Non-Destructive Anti-Hallucination Guardrail & Scalping Validator:
        1. PRESERVES Claude's genuine structural SL, TP1, TP2, TP3 & rationale when physically valid.
        2. Dynamically repairs ONLY invalid/hallucinated levels using live M15 ATR(14).
        3. Guarantees BUY physics: SL < entry_low <= entry_price <= entry_high < TP1 < TP2 < TP3.
        4. Guarantees SELL physics: SL > entry_high >= entry_price >= entry_low > TP1 > TP2 > TP3.
        5. Always recalculates exact pip distances and RRR from final prices (zero fake/mismatched pips).
        """
        if not isinstance(raw_data, dict):
            raw_data = {}

        m15 = m15_data or technical_data or {}
        atr_m15 = float(m15.get("atr_14") or (technical_data or {}).get("atr_14") or 3.50)
        session_name = str(m15.get("session_name") or (technical_data or {}).get("session_name") or "Global Session")

        # 1. Bias normalization
        bias = str(raw_data.get("bias", "NEUTRAL")).strip().upper()
        if bias not in ["BULLISH", "BEARISH", "NEUTRAL"]:
            bias = "NEUTRAL"

        # 2. Confidence Score
        try:
            confidence = int(raw_data.get("confidence_score", 72))
        except (ValueError, TypeError):
            confidence = 72
        confidence = max(55, min(95, confidence))

        # 3. Key Levels (Support & Resistance)
        key_levels = raw_data.get("key_levels", {})
        if not isinstance(key_levels, dict):
            key_levels = {}
        raw_sups = key_levels.get("support", [])
        raw_res = key_levels.get("resistance", [])

        valid_sups: List[float] = []
        if isinstance(raw_sups, list):
            for s in raw_sups:
                try:
                    sf = round(float(s), 2)
                    if (curr_price * 0.90) < sf < curr_price:
                        valid_sups.append(sf)
                except (ValueError, TypeError):
                    continue
        valid_sups = sorted(list(set(valid_sups)), reverse=True)
        if not valid_sups:
            tech_sups = m15.get("support_levels") or (technical_data or {}).get("support_levels") or []
            valid_sups = [round(float(s), 2) for s in tech_sups if (curr_price * 0.90) < float(s) < curr_price]
            if not valid_sups:
                valid_sups = [round(curr_price - max(4.0, atr_m15 * 1.5), 2), round(curr_price - max(9.0, atr_m15 * 3.0), 2)]

        valid_res: List[float] = []
        if isinstance(raw_res, list):
            for r in raw_res:
                try:
                    rf = round(float(r), 2)
                    if curr_price < rf < (curr_price * 1.10):
                        valid_res.append(rf)
                except (ValueError, TypeError):
                    continue
        valid_res = sorted(list(set(valid_res)))
        if not valid_res:
            tech_res = m15.get("resistance_levels") or (technical_data or {}).get("resistance_levels") or []
            valid_res = [round(float(r), 2) for r in tech_res if curr_price < float(r) < (curr_price * 1.10)]
            if not valid_res:
                valid_res = [round(curr_price + max(4.0, atr_m15 * 1.5), 2), round(curr_price + max(9.0, atr_m15 * 3.0), 2)]

        primary_sup = valid_sups[0]
        primary_res = valid_res[0]

        # 4. Trade Setup Validation (Preserves Claude levels when valid!)
        raw_setup = raw_data.get("trade_setup", {})
        if not isinstance(raw_setup, dict):
            raw_setup = {}

        action = str(raw_setup.get("action", "")).strip().upper()
        if action not in ["BUY", "SELL", "WAIT"]:
            action = "BUY" if bias == "BULLISH" else ("SELL" if bias == "BEARISH" else "WAIT")

        # Entry price anchored closely around live market price for scalping (max drift $3.00)
        try:
            entry_p = round(float(raw_setup.get("entry_price", curr_price)), 2)
            if abs(entry_p - curr_price) > 3.00 or entry_p <= 0:
                entry_p = round(curr_price, 2)
        except (ValueError, TypeError):
            entry_p = round(curr_price, 2)

        execution_type = str(raw_setup.get("execution_type", "")).strip().upper()
        if execution_type not in ["INSTANT", "LIMIT", "WAIT"]:
            if action == "WAIT":
                execution_type = "WAIT"
            else:
                execution_type = "INSTANT" if abs(entry_p - curr_price) <= 0.80 else "LIMIT"

        # Tight realistic scalping zone width ($1.20 - $2.00 full pocket)
        half_zone = round(max(0.60, min(1.00, atr_m15 * 0.22)), 2)
        default_risk = round(max(2.50, min(6.50, atr_m15 * 1.25)), 2)
        min_risk = 1.80
        max_risk = round(max(7.50, atr_m15 * 2.20), 2)

        def safe_float(val: Any) -> float:
            try:
                return round(float(val), 2)
            except (ValueError, TypeError):
                return 0.0

        ai_rationale = str(raw_setup.get("technical_rationale", "")).strip()
        ai_invalidation = str(raw_setup.get("invalidation_level", "")).strip()
        lot_mgmt = str(raw_setup.get("lot_management", "")).strip() or "40% TP1 (SL→BEP) • 40% TP2 (SL→TP1) • 20% Runner TP3"
        scalp_tf = str(raw_setup.get("scalp_timeframe", "")).strip() or "M5 / M15"

        if action == "BUY":
            entry_price = entry_p
            entry_low = round(entry_price - half_zone, 2)
            entry_high = round(entry_price + half_zone, 2)
            entry_zone = f"${entry_low:.2f} - ${entry_high:.2f}"
            action_label = str(raw_setup.get("action_label", "")).strip() or (
                "BUY NOW (SCALP)" if execution_type == "INSTANT" else "BUY LIMIT (PULLBACK)"
            )

            sl = safe_float(raw_setup.get("stop_loss"))
            if sl <= 0 or sl >= entry_low or (entry_price - sl) < min_risk or (entry_price - sl) > max_risk:
                sl = round(entry_price - default_risk, 2)
            risk = round(entry_price - sl, 2)

            tp1 = safe_float(raw_setup.get("take_profit_1"))
            if tp1 <= entry_high or (tp1 - entry_price) < max(1.80, risk * 0.70) or (tp1 - entry_price) > (risk * 2.0):
                tp1 = round(entry_price + max(2.50, risk * 1.00), 2)

            tp2 = safe_float(raw_setup.get("take_profit_2"))
            if tp2 <= (tp1 + 1.00) or (tp2 - entry_price) > (risk * 3.5):
                tp2 = round(max(tp1 + 2.00, entry_price + risk * 2.00), 2)

            tp3 = safe_float(raw_setup.get("take_profit_3"))
            if tp3 <= (tp2 + 1.20) or (tp3 - entry_price) > (risk * 5.5):
                tp3 = round(max(tp2 + 2.50, entry_price + risk * 3.20), 2)

            reward1 = round(tp1 - entry_price, 2)
            reward2 = round(tp2 - entry_price, 2)
            reward3 = round(tp3 - entry_price, 2)
            rrr = f"1 : {round(reward3 / risk, 1)}" if risk > 0 else "1 : 3.2"

            rationale = ai_rationale if len(ai_rationale) >= 25 else (
                f"Setup Direct BUY Scalp ({session_name}): Entry {entry_zone}, SL ${sl:.2f} (-{round(risk * 10):.0f} pips). "
                f"Amankan 40% di TP1 ${tp1:.2f} (+{round(reward1 * 10):.0f} pips, SL→BEP), "
                f"40% di TP2 ${tp2:.2f} (+{round(reward2 * 10):.0f} pips, SL→TP1), "
                f"dan 20% runner menuju TP3 ${tp3:.2f} (+{round(reward3 * 10):.0f} pips)."
            )
            invalidation = ai_invalidation if len(ai_invalidation) >= 12 else (
                f"Close candle M15 di bawah ${sl:.2f} membatalkan setup BUY scalp."
            )

        elif action == "SELL":
            entry_price = entry_p
            entry_low = round(entry_price - half_zone, 2)
            entry_high = round(entry_price + half_zone, 2)
            entry_zone = f"${entry_low:.2f} - ${entry_high:.2f}"
            action_label = str(raw_setup.get("action_label", "")).strip() or (
                "SELL NOW (SCALP)" if execution_type == "INSTANT" else "SELL LIMIT (RALLY)"
            )

            sl = safe_float(raw_setup.get("stop_loss"))
            if sl <= 0 or sl <= entry_high or (sl - entry_price) < min_risk or (sl - entry_price) > max_risk:
                sl = round(entry_price + default_risk, 2)
            risk = round(sl - entry_price, 2)

            tp1 = safe_float(raw_setup.get("take_profit_1"))
            if tp1 <= 0 or tp1 >= entry_low or (entry_price - tp1) < max(1.80, risk * 0.70) or (entry_price - tp1) > (risk * 2.0):
                tp1 = round(entry_price - max(2.50, risk * 1.00), 2)

            tp2 = safe_float(raw_setup.get("take_profit_2"))
            if tp2 <= 0 or tp2 >= (tp1 - 1.00) or (entry_price - tp2) > (risk * 3.5):
                tp2 = round(min(tp1 - 2.00, entry_price - risk * 2.00), 2)

            tp3 = safe_float(raw_setup.get("take_profit_3"))
            if tp3 <= 0 or tp3 >= (tp2 - 1.20) or (entry_price - tp3) > (risk * 5.5):
                tp3 = round(min(tp2 - 2.50, entry_price - risk * 3.20), 2)

            reward1 = round(entry_price - tp1, 2)
            reward2 = round(entry_price - tp2, 2)
            reward3 = round(entry_price - tp3, 2)
            rrr = f"1 : {round(reward3 / risk, 1)}" if risk > 0 else "1 : 3.2"

            rationale = ai_rationale if len(ai_rationale) >= 25 else (
                f"Setup Direct SELL Scalp ({session_name}): Entry {entry_zone}, SL ${sl:.2f} (-{round(risk * 10):.0f} pips). "
                f"Amankan 40% di TP1 ${tp1:.2f} (+{round(reward1 * 10):.0f} pips, SL→BEP), "
                f"40% di TP2 ${tp2:.2f} (+{round(reward2 * 10):.0f} pips, SL→TP1), "
                f"dan 20% runner menuju TP3 ${tp3:.2f} (+{round(reward3 * 10):.0f} pips)."
            )
            invalidation = ai_invalidation if len(ai_invalidation) >= 12 else (
                f"Close candle M15 di atas ${sl:.2f} membatalkan setup SELL scalp."
            )

        else:
            action = "WAIT"
            execution_type = "WAIT"
            action_label = str(raw_setup.get("action_label", "")).strip() or "WAIT / NEWS GUARD"
            entry_price = round(curr_price, 2)
            entry_zone = str(raw_setup.get("entry_zone", "")).strip() or f"Breakout > ${primary_res:.2f} / < ${primary_sup:.2f}"
            sl = round(entry_price - default_risk, 2)
            tp1 = round(entry_price + default_risk * 1.0, 2)
            tp2 = round(entry_price + default_risk * 2.0, 2)
            tp3 = round(entry_price + default_risk * 3.2, 2)
            risk = default_risk
            reward1 = round(tp1 - entry_price, 2)
            reward2 = round(tp2 - entry_price, 2)
            reward3 = round(tp3 - entry_price, 2)
            rrr = f"1 : {round(reward3 / risk, 1)}" if risk > 0 else "1 : 3.2"
            rationale = ai_rationale if len(ai_rationale) >= 20 else (
                f"Menunggu konfirmasi breakout dari area ${primary_sup:.2f}–${primary_res:.2f} agar terhindar dari whipsaw."
            )
            invalidation = ai_invalidation if len(ai_invalidation) >= 10 else "Lonjakan spread & whipsaw news."

        mode_hint = (
            "Siap Eksekusi Langsung"
            if execution_type == "INSTANT"
            else ("Tunggu Pullback ke Zona" if execution_type == "LIMIT" else "Standby / News Guard")
        )

        trade_setup = {
            "action": action,
            "action_label": action_label,
            "execution_type": execution_type,
            "scalp_timeframe": scalp_tf,
            "session_name": session_name,
            "atr_pips": round(atr_m15 * 10.0, 1),
            "entry_zone": entry_zone,
            "entry_price": entry_price,
            "stop_loss": sl,
            "take_profit_1": tp1,
            "take_profit_2": tp2,
            "take_profit_3": tp3,
            "risk_reward_ratio": rrr,
            "risk_pips": round(risk * 10.0, 1),
            "reward_tp1_pips": round(reward1 * 10.0, 1),
            "reward_tp2_pips": round(reward2 * 10.0, 1),
            "reward_tp3_pips": round(reward3 * 10.0, 1),
            "lot_management": lot_mgmt,
            "technical_rationale": str(rationale),
            "invalidation_level": str(invalidation),
            "status": "ACTIVE",
            "status_message": f"{action_label} • {mode_hint} (Acuan ${entry_price:.2f} | ATR {round(atr_m15 * 10, 1)} pips)",
        }

        # 5. Clean Summaries & Notes
        summary = str(raw_data.get("summary", "")).strip() or (
            f"Analisis multi-timeframe {symbol} mengonfirmasi bias {bias} ({confidence}%) pada sesi {session_name} di sekitar ${curr_price:.2f}."
        )
        fund_notes = str(raw_data.get("fundamental_notes", "")).strip() or (
            "Kebijakan suku bunga The Fed, data inflasi/tenaga kerja AS, serta arah DXY & Yield US10Y menjadi katalis fundamental utama."
        )
        geo_notes = str(raw_data.get("geopolitical_notes", "")).strip() or (
            "Arus berita geopolitik global dan permintaan aset safe-haven menopang likuiditas emas intraday."
        )
        tech_notes = str(raw_data.get("technical_notes", "")).strip() or (
            f"Struktur M15/H1 memantau Support ${primary_sup:.2f} dan Resistance ${primary_res:.2f} dengan ATR M15 {round(atr_m15 * 10, 1)} pips."
        )

        # 6. Risk factors & Sources
        raw_risks = raw_data.get("risk_factors", [])
        risks = [str(r) for r in raw_risks if str(r).strip()][:4] if isinstance(raw_risks, list) and raw_risks else [
            "Volatilitas tajam saat rilis berita High-Impact AS berpotensi memicu sweep likuiditas.",
            f"Penembusan candle M15 melewati level invalidasi ${sl:.2f} membatalkan setup.",
        ]

        raw_sources = raw_data.get("sources", [])
        sources = [str(s) for s in raw_sources if str(s).strip()][:4] if isinstance(raw_sources, list) and raw_sources else [
            f"Multi-Timeframe M5/M15/H1 & ATR(14) ({round(atr_m15 * 10, 1)} pips)",
            "Kalender Ekonomi ForexFactory",
            "Arus Berita Global & Geopolitik XAU/USD",
        ]

        return {
            "bias": bias,
            "confidence_score": confidence,
            "summary": summary,
            "fundamental_notes": fund_notes,
            "geopolitical_notes": geo_notes,
            "technical_notes": tech_notes,
            "key_levels": {
                "support": valid_sups[:2],
                "resistance": valid_res[:2],
            },
            "trade_setup": trade_setup,
            "risk_factors": risks,
            "sources": sources,
        }
