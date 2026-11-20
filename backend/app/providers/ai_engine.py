import json
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah Senior Institutional XAU/USD Top-Down Multi-Timeframe (M1–D1) Scalping Strategist.
Tugas utamamu: membandingkan SEMUA 7 sudut pandang timeframe (M1, M5, M15, M30, H1, H4, D1), mencari ZONA KONFLUENSI (zona Support/Resistance yang saling bertumpuk di beberapa timeframe sekaligus), ATR volatilitas, sesi aktif, kalender ekonomi, dan berita global untuk menghasilkan SETUP SCALPING SIAP EKSEKUSI (Entry, SL, TP1, TP2, TP3) yang presisi.

ATURAN MUTLAK INTEGRITAS DATA & ZERO-HALLUCINATION:
1. HARGA AKTIF PASAR: Seluruh angka harga (Entry, SL, TP1, TP2, TP3, Support, Resistance) WAJIB berpatokan langsung pada `current_price` di JSON input. JANGAN PERNAH memakai harga lama/halusinasi.
2. HUKUM FISIKA TRADING (WAJIB 100% VALID):
   - BUY: `stop_loss < entry_low <= entry_price <= entry_high < take_profit_1 < take_profit_2 < take_profit_3`
   - SELL: `stop_loss > entry_high >= entry_price >= entry_low > take_profit_1 > take_profit_2 > take_profit_3`
3. ANALISIS TOP-DOWN 7 TIMEFRAME (BANDINGKAN SEMUA SUDUT PANDANG!):
   - **D1 & H4 (HTF — Arah Makro & Tembok Besar)**: Pastikan kamu tahu arah besar dan tidak sembarangan entry menabrak tembok Supply/Demand major H4/D1.
   - **H1 & M30 (ITF — Struktur Intraday & Zona Utama)**: Petakan struktur swing dan zona pullback intraday.
   - **M15 & M5 (Setup TF — Zona Entry & ATR)**: Kalibrasi lebar zona entry & Stop Loss menggunakan `atr_14` M15 dan swing structure.
   - **M1 (LTF — Sniper Trigger)**: Cek apakah M1 sudah konfirmasi reaksi untuk `execution_type: "INSTANT"` (eksekusi langsung) atau masih terlalu jauh sehingga lebih baik `"LIMIT"` menunggu pullback tipis ke zona konfluensi!
   - **ZONA KONFLUENSI LINTAS TIMEFRAME**: Perhatikan `confluence_demand_zones` dan `confluence_supply_zones` di input JSON — zona yang disepakati 2–4 timeframe sekaligus adalah zona entry & TP terbaik!
   - Hanya gunakan `WAIT` jika ada rilis berita HIGH-IMPACT USD (NFP/CPI/FOMC/PCE) kurang dari 15 menit lagi.
   - **ZONA ENTRY KETAT**: Lebar maksimal 10–20 pips ($1.00–$2.00) di dekat `current_price` atau zona konfluensi terdekat.
   - **STOP LOSS (SL) DINAMIS BERBASIS ATR & SWING**:
     * Di balik swing low/high M5–M15/M30 terdekat (kisaran ideal 25–65 pips / $2.50–$6.50 disesuaikan ATR sesi).
   - **3-TIER TAKE PROFIT SCALING (WAJIB LENGKAP TP1, TP2, TP3)**:
     * **TP1 (Quick Scalp — Amankan 40% Lot)**: ~0.9x–1.2x jarak SL → langsung geser SL ke Breakeven (BEP).
     * **TP2 (Main Intraday Target — Amankan 40% Lot)**: ~1.8x–2.3x jarak SL di area konfluensi M15/M30/H1 → geser SL ke TP1.
     * **TP3 (Extended Runner — Tahan 20% Lot)**: ~2.8x–3.8x jarak SL di area likuiditas H1/H4.
4. BAHASA & RINGKASAN:
   - Bahasa Indonesia profesional, tajam, taktis, langsung menjelaskan perbandingan timeframe (HTF vs ITF vs LTF).

OUTPUT HARUS BERUPA JSON VALID MURNI TANPA MARKDOWN WRAPPER:
{
  "bias": "BULLISH" | "BEARISH" | "NEUTRAL",
  "confidence_score": integer (55-95),
  "summary": "Ringkasan bias 2 kalimat yang membandingkan arah HTF (D1/H4/H1) vs LTF (M30/M15/M5/M1), sesi aktif, dan makro.",
  "fundamental_notes": "Dampak agenda kalender ekonomi terdekat, suku bunga Fed, Yield US10Y & DXY.",
  "geopolitical_notes": "Dampak sentimen berita global & safe-haven terkini ke permintaan emas.",
  "technical_notes": "Perbandingan sudut pandang D1/H4 (makro) vs H1/M30 (struktur) vs M15/M5/M1 (zona entry & konfluensi).",
  "key_levels": {
    "support": [number, number],
    "resistance": [number, number]
  },
  "trade_setup": {
    "action": "BUY" | "SELL" | "WAIT",
    "action_label": "BUY NOW (SCALP)" | "BUY LIMIT (PULLBACK)" | "SELL NOW (SCALP)" | "SELL LIMIT (RALLY)" | "WAIT / NEWS GUARD",
    "execution_type": "INSTANT" | "LIMIT" | "WAIT",
    "scalp_timeframe": "M1–D1 MTF",
    "entry_zone": "$3562.50 - $3564.20",
    "entry_price": 3563.50,
    "stop_loss": 3559.70,
    "take_profit_1": 3567.30,
    "take_profit_2": 3571.50,
    "take_profit_3": 3576.50,
    "lot_management": "40% TP1 (SL→BEP) • 40% TP2 (SL→TP1) • 20% Runner TP3",
    "confluence_note": "Penjelasan 1 kalimat timeframe mana saja yang sepakat di zona entry & perbandingan HTF vs LTF.",
    "technical_rationale": "Alasan spesifik berbasis perbandingan 7 timeframe (M1–D1), zona konfluensi, ATR, dan scaling TP1-TP2-TP3.",
    "invalidation_level": "Close candle M15 di bawah $3559.70 membatalkan setup ini."
  },
  "risk_factors": [
    "Faktor risiko 1",
    "Faktor risiko 2"
  ],
  "sources": [
    "Analisis Top-Down 7 Timeframe (M1, M5, M15, M30, H1, H4, D1) & ATR(14)",
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
        mtf = mtf_technical or {}
        m1_tech = mtf.get("1m") or mtf.get("5m") or technical_data
        m5_tech = mtf.get("5m") or technical_data
        m15_tech = mtf.get("15m") or technical_data
        m30_tech = mtf.get("30m") or m15_tech
        h1_tech = mtf.get("1h") or technical_data
        h4_tech = mtf.get("4h") or h1_tech
        d1_tech = mtf.get("1d") or h4_tech
        confluence = mtf.get("confluence") or {}

        payload_data = {
            "symbol": symbol,
            "current_price": curr_price,
            "session": m15_tech.get("session_name", "Global Session"),
            "session_volatility": m15_tech.get("session_volatility", "MEDIUM"),
            "top_down_alignment": {
                "alignment_label": confluence.get("alignment_label", ""),
                "htf_bias_d1_h4_h1": confluence.get("htf_bias", h1_tech.get("trend_direction")),
                "itf_bias_m30_m15": confluence.get("itf_bias", m15_tech.get("trend_direction")),
                "ltf_bias_m5_m1": confluence.get("ltf_bias", m5_tech.get("trend_direction")),
                "mtf_score": confluence.get("mtf_score", 0.0),
            },
            "all_7_timeframes_comparison": confluence.get("overview", []),
            "confluence_demand_zones": confluence.get("confluence_supports", []),
            "confluence_supply_zones": confluence.get("confluence_resistances", []),
            "execution_detail": {
                "m1_trigger": {"trend": m1_tech.get("trend_direction"), "rsi": m1_tech.get("rsi_14"), "ema9": m1_tech.get("ema_9"), "pa": m1_tech.get("price_action")},
                "m5_structure": {"trend": m5_tech.get("trend_direction"), "rsi": m5_tech.get("rsi_14"), "ema9": m5_tech.get("ema_9"), "ema21": m5_tech.get("ema_21"), "pa": m5_tech.get("price_action_note")},
                "m15_atr_swings": {"atr_14": m15_tech.get("atr_14"), "atr_pips": m15_tech.get("atr_pips"), "swing_lows": m15_tech.get("swing_lows", []), "swing_highs": m15_tech.get("swing_highs", [])},
                "m30_h1_intraday": {"m30_trend": m30_tech.get("trend_direction"), "h1_trend": h1_tech.get("trend_direction"), "h4_trend": h4_tech.get("trend_direction"), "d1_trend": d1_tech.get("trend_direction")},
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
                    mtf_technical=mtf,
                    economic_events=economic_events,
                    news_articles=news_articles,
                )
                logger.info("[AIAgentEngine] Claude 7-TF MTF scalping analysis synthesized & validated!")
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
                    mtf_technical=mtf,
                    economic_events=economic_events,
                    news_articles=news_articles,
                )
                logger.info("[AIAgentEngine] Gemini 7-TF scalping analysis synthesized & validated!")
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
                    mtf_technical=mtf,
                    economic_events=economic_events,
                    news_articles=news_articles,
                )
                logger.info("[AIAgentEngine] OpenRouter 7-TF scalping analysis synthesized & validated!")
                return sanitized
            except Exception as e:
                logger.warning(f"OpenRouter API failed, falling back to quantitative 7-TF scalping engine: {e}")

        # 4. Built-in 7-Timeframe ATR & Confluence Quantitative Direct Scalping Engine
        raw_heuristic = AIAgentEngine._heuristic_synthesis(
            symbol=symbol,
            price_snapshot=price_snapshot,
            technical_data=h1_tech,
            economic_events=economic_events,
            news_articles=news_articles,
            m15_data=m15_tech,
            m5_data=m5_tech,
            mtf_technical=mtf,
        )
        return AIAgentEngine._sanitize_and_validate_trade_setup(
            raw_heuristic,
            curr_price=curr_price,
            technical_data=h1_tech,
            m15_data=m15_tech,
            m5_data=m5_tech,
            mtf_technical=mtf,
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
        mtf_technical: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Quantitative 7-Timeframe Top-Down (M1, M5, M15, M30, H1, H4, D1) Confluence Scalping Synthesizer.
        Weights HTF macro structure (D1/H4/H1), ITF intraday swings (M30/M15), and LTF sniper triggers (M5/M1).
        """
        curr_price = float(price_snapshot.get("current_price", 0.0) or technical_data.get("latest_price", 3560.0))
        mtf = mtf_technical or {}
        m1 = mtf.get("1m") or m5_data or technical_data
        m15 = m15_data or mtf.get("15m") or technical_data
        m5 = m5_data or mtf.get("5m") or m15
        m30 = mtf.get("30m") or m15
        h4 = mtf.get("4h") or technical_data
        d1 = mtf.get("1d") or h4
        confluence = mtf.get("confluence") or {}

        # 1. 7-Timeframe Weighted Technical Score (-1.0 to +1.0)
        def dir_to_score(d: str) -> float:
            u = str(d or "").upper()
            return 0.85 if u == "BULLISH" else (-0.85 if u == "BEARISH" else 0.0)

        if "mtf_score" in confluence:
            base_mtf = float(confluence["mtf_score"])
        else:
            base_mtf = (
                dir_to_score(d1.get("trend_direction", "SIDEWAYS")) * 0.20
                + dir_to_score(h4.get("trend_direction", "SIDEWAYS")) * 0.18
                + dir_to_score(technical_data.get("trend_direction", "SIDEWAYS")) * 0.17
                + dir_to_score(m30.get("trend_direction", "SIDEWAYS")) * 0.15
                + dir_to_score(m15.get("trend_direction", "SIDEWAYS")) * 0.13
                + dir_to_score(m5.get("trend_direction", "SIDEWAYS")) * 0.10
                + dir_to_score(m1.get("trend_direction", "SIDEWAYS")) * 0.07
            )

        # Add Price Action micro-trigger nudge on M1/M5/M15
        pa = str(m1.get("price_action") or m5.get("price_action") or m15.get("price_action") or "").upper()
        pa_boost = 0.0
        if pa in ("BULLISH_REJECTION", "BULLISH_ENGULFING", "BULLISH_IMPULSE"):
            pa_boost = 0.25
        elif pa in ("BEARISH_REJECTION", "BEARISH_ENGULFING", "BEARISH_IMPULSE"):
            pa_boost = -0.25

        # Add RSI oversold/overbought scalping edge
        m15_rsi = m15.get("rsi_14")
        rsi_edge = 0.0
        if isinstance(m15_rsi, (int, float)):
            if m15_rsi <= 34:
                rsi_edge = 0.28
            elif m15_rsi >= 66:
                rsi_edge = -0.28
            elif 52 <= m15_rsi < 66:
                rsi_edge = 0.12
            elif 34 < m15_rsi <= 48:
                rsi_edge = -0.12

        tech_score = max(-1.0, min(1.0, base_mtf + pa_boost + rsi_edge))

        # 2. Geopolitical Sentiment Score (-1.0 to 1.0)
        news_scores = [float(n.get("sentiment_score", 0.0) or 0.0) for n in news_articles]
        geo_score = sum(news_scores) / len(news_scores) if news_scores else 0.0

        # 3. Fundamental Score (-1.0 to 1.0)
        fund_score = 0.10
        for event in economic_events:
            impact = str(event.get("sentiment_impact", "") or "").upper()
            if "BULLISH_GOLD" in impact or "BEARISH_USD" in impact:
                fund_score += 0.25
            elif "BEARISH_GOLD" in impact or "BULLISH_USD" in impact:
                fund_score -= 0.25
        fund_score = max(-1.0, min(1.0, fund_score))

        # Weighted Composite Score
        composite_score = (tech_score * 0.60) + (fund_score * 0.22) + (geo_score * 0.18)

        # Confluence Support & Resistance from all 7 TFs
        conf_sups = confluence.get("confluence_supports") or []
        conf_ress = confluence.get("confluence_resistances") or []
        supports = [c["price"] for c in conf_sups] or m15.get("support_levels") or technical_data.get("support_levels") or [round(curr_price - 8.0, 2)]
        resistances = [c["price"] for c in conf_ress] or m15.get("resistance_levels") or technical_data.get("resistance_levels") or [round(curr_price + 8.0, 2)]
        nearest_sup = max([s for s in supports if s < curr_price], default=round(curr_price - 8.0, 2))
        nearest_res = min([r for r in resistances if r > curr_price], default=round(curr_price + 8.0, 2))
        dist_sup = curr_price - nearest_sup
        dist_res = nearest_res - curr_price

        if abs(composite_score) < 0.18:
            if dist_sup < dist_res * 0.65 and dist_sup <= 8.0:
                composite_score += 0.22
            elif dist_res < dist_sup * 0.65 and dist_res <= 8.0:
                composite_score -= 0.22

        session_name = m15.get("session_name", "Global Session")
        align_label = confluence.get("alignment_label", "MTF 7-TF")

        if composite_score >= 0.12:
            bias = "BULLISH"
            confidence = int(64 + min(30, abs(composite_score) * 32))
            summary = (
                f"Perbandingan 7 timeframe ({align_label}) pada {session_name} mengonfirmasi bias BUY {symbol} "
                f"dengan zona konfluensi demand di sekitar ${nearest_sup:.2f}."
            )
        elif composite_score <= -0.12:
            bias = "BEARISH"
            confidence = int(64 + min(30, abs(composite_score) * 32))
            summary = (
                f"Perbandingan 7 timeframe ({align_label}) pada {session_name} mengonfirmasi bias SELL {symbol} "
                f"dengan zona konfluensi supply di sekitar ${nearest_res:.2f}."
            )
        else:
            bias = "BULLISH" if (dist_sup <= dist_res) else "BEARISH"
            confidence = 60
            summary = (
                f"Sudut pandang lintas timeframe ({align_label}) menunjukkan konsolidasi ${nearest_sup:.2f}–${nearest_res:.2f}; "
                f"setup scalping taktis diarahkan ke sisi {bias} dengan SL struktural ketat."
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
            mtf_technical=mtf,
            economic_events=economic_events,
            news_articles=news_articles,
        )

        sources = [
            f"Perbandingan Top-Down 7 Timeframe (M1–D1: {align_label})",
            f"Sesi {session_name} • ATR M15 {m15.get('atr_pips', 35.0)} pips",
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
                f"HTF (D1 {d1.get('trend_direction', '-')}, H4 {h4.get('trend_direction', '-')}, H1 {technical_data.get('trend_direction', '-')}) | "
                f"ITF (M30 {m30.get('trend_direction', '-')}, M15 {m15.get('trend_direction', '-')}) | "
                f"LTF (M5 {m5.get('trend_direction', '-')}, M1 {m1.get('trend_direction', '-')}). "
                f"{confluence.get('confluence_note', '')}"
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
        mtf_technical: Optional[Dict[str, Any]] = None,
        economic_events: Optional[List[Dict[str, Any]]] = None,
        news_articles: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        7-Timeframe Confluence & ATR-Calibrated Direct Scalping Engine (SL + TP1 + TP2 + TP3).
        Reconciles M1/M5/M15/M30/H1/H4/D1 zones so entry sits at the strongest overlapping cluster.
        """
        mtf = mtf_technical or {}
        m1 = mtf.get("1m") or m5_data or technical_data
        m15 = m15_data or mtf.get("15m") or technical_data
        m5 = m5_data or mtf.get("5m") or m15
        confluence = mtf.get("confluence") or {}
        conf_sups = confluence.get("confluence_supports") or []
        conf_ress = confluence.get("confluence_resistances") or []
        align_label = str(confluence.get("alignment_label") or "MTF 7-TF")
        conf_note = str(confluence.get("confluence_note") or "")
        mtf_overview = confluence.get("overview") or []

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
            # Direct Instant Scalp if HTF/ITF/LTF align (including M1 trigger), else tight pullback to confluence cluster
            m1_bull = str(m1.get("trend_direction", "")).upper() == "BULLISH"
            all_ltf_bull = m1_bull and str(m5.get("trend_direction", "")).upper() == "BULLISH"
            near_ema = ema9_m5 is not None and abs(curr_price - float(ema9_m5)) <= (atr_m15 * 0.65)
            near_sup = bool(swing_lows) and (curr_price - swing_lows[0]) <= (atr_m15 * 1.1)
            is_instant = all_ltf_bull or near_ema or near_sup or str(m1.get("price_action", "")).startswith("BULLISH")

            # Check if a strong multi-TF Confluence Support cluster sits right below price (within $2.20)
            best_conf_sup = next((c for c in conf_sups if c["tf_count"] >= 2 and 0.30 <= (curr_price - c["price"]) <= 2.20), None)

            if is_instant and not best_conf_sup:
                execution_type = "INSTANT"
                action_label = "BUY NOW (SCALP)"
                entry_price = round(curr_price, 2)
            elif best_conf_sup:
                execution_type = "LIMIT"
                action_label = "BUY LIMIT (CONFLUENCE)"
                entry_price = round(float(best_conf_sup["price"]), 2)
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
            m1_bear = str(m1.get("trend_direction", "")).upper() == "BEARISH"
            all_ltf_bear = m1_bear and str(m5.get("trend_direction", "")).upper() == "BEARISH"
            near_ema = ema9_m5 is not None and abs(curr_price - float(ema9_m5)) <= (atr_m15 * 0.65)
            near_res = bool(swing_highs) and (swing_highs[0] - curr_price) <= (atr_m15 * 1.1)
            is_instant = all_ltf_bear or near_ema or near_res or str(m1.get("price_action", "")).startswith("BEARISH")

            best_conf_res = next((c for c in conf_ress if c["tf_count"] >= 2 and 0.30 <= (c["price"] - curr_price) <= 2.20), None)

            if is_instant and not best_conf_res:
                execution_type = "INSTANT"
                action_label = "SELL NOW (SCALP)"
                entry_price = round(curr_price, 2)
            elif best_conf_res:
                execution_type = "LIMIT"
                action_label = "SELL LIMIT (CONFLUENCE)"
                entry_price = round(float(best_conf_res["price"]), 2)
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
            "scalp_timeframe": "M1–D1 MTF",
            "session_name": session_name,
            "atr_pips": round(atr_m15 * 10.0, 1),
            "mtf_alignment": align_label,
            "mtf_overview": mtf_overview,
            "confluence_note": conf_note,
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
        mtf_technical: Optional[Dict[str, Any]] = None,
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
        scalp_tf = str(raw_setup.get("scalp_timeframe", "")).strip() or "M1–D1 MTF"
        confluence = (mtf_technical or {}).get("confluence") or {}
        mtf_overview = confluence.get("overview") or raw_setup.get("mtf_overview") or []
        mtf_alignment = str(confluence.get("alignment_label") or raw_setup.get("mtf_alignment") or "M1–D1 MTF")
        confluence_note = str(raw_setup.get("confluence_note") or confluence.get("confluence_note") or "").strip()

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
            "mtf_alignment": mtf_alignment,
            "mtf_overview": mtf_overview,
            "confluence_note": confluence_note,
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
