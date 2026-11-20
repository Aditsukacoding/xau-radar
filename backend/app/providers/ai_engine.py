import json
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah Senior Institutional XAU/USD Top-Down Multi-Timeframe (M1–D1) Sniper Scalping Strategist.
Tugas utamamu: membandingkan SEMUA 7 sudut pandang timeframe (M1, M5, M15, M30, H1, H4, D1), mencari ZONA KONFLUENSI (zona Support/Resistance yang saling bertumpuk di beberapa timeframe sekaligus), ATR volatilitas, sesi aktif, kalender ekonomi, dan berita global untuk menghasilkan SETUP SNIPER SCALPING SIAP EKSEKUSI (Entry, SL, TP1, TP2, TP3) dengan alasan yang transparan dan mudah dipahami trader.

ATURAN MUTLAK INTEGRITAS DATA, PROFIL SNIPER & ZERO-HALLUCINATION:
1. HARGA AKTIF PASAR: Seluruh angka harga (Entry, SL, TP1, TP2, TP3, Support, Resistance) WAJIB berpatokan langsung pada `current_price` di JSON input. JANGAN PERNAH memakai harga lama/halusinasi.
2. HUKUM FISIKA TRADING (WAJIB 100% VALID):
   - BUY: `stop_loss < entry_low <= entry_price <= entry_high < take_profit_1 < take_profit_2 < take_profit_3`
   - SELL: `stop_loss > entry_high >= entry_price >= entry_low > take_profit_1 > take_profit_2 > take_profit_3`
3. ANALISIS TOP-DOWN 7 TIMEFRAME (BANDINGKAN SEMUA SUDUT PANDANG!):
   - **D1 & H4 (HTF — Arah Makro & Tembok Besar)**: Ketahui arah tren besar & tembok Supply/Demand major agar tidak entry menabrak tembok besar.
   - **H1 & M30 (ITF — Struktur Intraday & Zona Utama)**: Petakan struktur swing dan target TP2/TP3.
   - **M15 & M5 (Setup TF — Zona Sniper & Swing)**: Cari tepi zona pullback/konfluensi agar Stop Loss ketat terlindungi di balik struktur.
   - **M1 (LTF — Sniper Trigger)**: Cek apakah M1 sudah konfirmasi reaksi tepat di zona (`"INSTANT"`) atau harga sudah lari jauh sehingga WAJIB `"LIMIT"` menunggu pullback/retest tipis (ANTI-KEJAR HARGA!).
   - Hanya gunakan `WAIT` jika ada rilis berita HIGH-IMPACT USD (NFP/CPI/FOMC/PCE) kurang dari 15 menit lagi.
4. PROFIL KEY-ZONE SNIPER SCALPING USER (WAJIB DIPATUHI):
   - Konvensi pip XAU/USD: `10 pips = $1.00` (jadi `30–50 pips = $3.00–$5.00`, `60 pips = $6.00`).
   - **JANGAN MENCARI ZONA TERLALU DEKAT SPOT (< 45 PIPS / RAWAN SWEEP!)**:
     * JANGAN membuat zona entry buatan yang mepet harga spot saat harga melayang di ruang kosong atau sudah jenuh (RSI oversold di dasar / overbought di puncak)!
     * WAJIB pilih **KEY STRUCTURAL ZONE ASLI** dari `confluence_supply_zones` (untuk SELL) atau `confluence_demand_zones` (untuk BUY) — utamakan zona yang punya reaksi berulang (`touches >= 2` / `rejections >= 2` / Flip SBR-RBS) pada jarak aman **45–420 pips ($4.50–$42.00)** dari `current_price` menggunakan `"LIMIT"` (`BUY LIMIT (KEY ZONE)` / `SELL LIMIT (KEY ZONE)`).
     * Gunakan `"INSTANT"` HANYA jika `current_price` memang SEDANG menyentuh (<= 18 pips) Key Zone multi-TF yang teruji kuat + konfirmasi candle M1/M5!
   - **STOP LOSS (SL) KETAT SNIPER: WAJIB 30–50 PIPS ($3.00–$5.00)**:
     * Diletakkan persis di luar ekor zona Supply/Demand tersebut (`30–40p` sesi tenang, `40–50p` sesi aktif). JANGAN melebihi 50 pips!
   - **3-TIER TAKE PROFIT SCALING (WAJIB LENGKAP TP1, TP2, TP3)**:
     * **TP1 (Wajib 60 Pips / $6.00 — Amankan 40% Lot)**: Tepat +60 pips dari `entry_price` (RRR TP1 = 1:1.2 s/d 1:2.0) → langsung geser SL ke Breakeven (BEP).
     * **TP2 (Struktur Lawan Asli — Amankan 40% Lot)**: Membidik zona Support/Resistance struktural utama (M15/M30/H1) → geser SL ke TP1.
     * **TP3 (Extended Runner — Tahan 20% Lot)**: Membidik tembok likuiditas major H1/H4/D1 berikutnya.
5. BAHASA, BUKTI ZONA & ALASAN ENTRY:
   - Bahasa Indonesia lugas, ramah pembaca, langsung ke inti alasan ("kenapa menunggu zona ini, bukti reaksinya apa, kenapa SL di situ, kenapa TP di sana").
   - WAJIB sertakan `setup_quality_score` (55–96), `zone_proof` (bukti jumlah sentuhan/penolakan & TF konfluensi dari JSON), dan array `entry_reasons` tepat 4 poin.

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
    "action_label": "BUY LIMIT (KEY ZONE)" | "SELL LIMIT (KEY ZONE)" | "BUY NOW (KEY ZONE)" | "SELL NOW (KEY ZONE)" | "WAIT • NEWS GUARD",
    "execution_type": "LIMIT" | "INSTANT" | "WAIT",
    "scalp_timeframe": "M1–D1 MTF",
    "setup_quality_score": 82,
    "zone_proof": "Diuji 5× (3× penolakan kuat) • Supply/Flip M5+M15+M30",
    "entry_zone": "$3554.80 - $3556.50",
    "entry_price": 3555.50,
    "stop_loss": 3560.00,
    "take_profit_1": 3549.50,
    "take_profit_2": 3538.50,
    "take_profit_3": 3529.00,
    "lot_management": "40% TP1 +60p (SL→BEP) • 40% TP2 (SL→TP1) • 20% Runner TP3",
    "confluence_note": "Penjelasan 1 kalimat timeframe mana saja yang sepakat di Key Zone Demand & Supply terkuat.",
    "entry_reasons": [
      {"title": "Arah 7 Timeframe", "tag": "6/7 BEARISH", "tone": "bearish", "detail": "Penjelasan singkat keselarasan HTF (D1/H4/H1), ITF (M30/M15), dan LTF (M5/M1)."},
      {"title": "Alasan Key Zone", "tag": "LIMIT KEY ZONE", "tone": "cyan", "detail": "Menunggu di zona Supply/Demand asli (tidak terlalu dekat spot) dengan bukti reaksi berulang."},
      {"title": "Proteksi SL Ketat", "tag": "-45 pips", "tone": "bearish", "detail": "SL ditaruh tepat di luar ekor zona Supply/Demand dalam batas ketat 30–50 pips."},
      {"title": "Target TP1–TP3", "tag": "TP1 +60p", "tone": "bullish", "detail": "TP1 +60 pips langsung kunci 40% & BEP, TP2 & TP3 membidik level struktur lawan asli."}
    ],
    "technical_rationale": "Ringkasan 2 kalimat utuh alasan setup Key-Zone Sniper berdasarkan 7 timeframe, bukti reaksi zona, dan risk management.",
    "invalidation_level": "Close candle M15 di atas $3560.00 membatalkan setup ini."
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
        macro_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes multi-timeframe scalping + 3-pillar data using:
        1. Anthropic Claude API (Sonnet 4.5 / Haiku 4.5) when valid ANTHROPIC_API_KEY is configured
        2. Gemini API (if configured)
        3. OpenRouter AI Gateway (if configured)
        4. Built-in ATR & Multi-Timeframe Quantitative Key-Zone Sniper Engine + Macro/Intermarket
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
        mctx = macro_context or {}

        payload_data = {
            "symbol": symbol,
            "current_price": curr_price,
            "session": m15_tech.get("session_name", "Global Session"),
            "session_volatility": m15_tech.get("session_volatility", "MEDIUM"),
            "intermarket_live": mctx.get("intermarket", {}),
            "economic_surprise_analysis": mctx.get("fundamental", {}),
            "geopolitical_intelligence": mctx.get("geopolitical", {}),
            "historical_news_reactions": mctx.get("historical_reactions", {}),
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
            "upcoming_and_recent_economic_events": economic_events[:10],
            "recent_news_sentiment": news_articles[:8],
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

        # 4. Built-in 7-Timeframe ATR & Confluence Quantitative Key-Zone Sniper Engine + Live Macro
        raw_heuristic = AIAgentEngine._heuristic_synthesis(
            symbol=symbol,
            price_snapshot=price_snapshot,
            technical_data=h1_tech,
            economic_events=economic_events,
            news_articles=news_articles,
            m15_data=m15_tech,
            m5_data=m5_tech,
            mtf_technical=mtf,
            macro_context=mctx,
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
        macro_context: Optional[Dict[str, Any]] = None,
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

        # 2. Geopolitical Sentiment Score (-1.0 to 1.0) — Time-Decayed, Theme-Aware & Contrast-Safe
        mctx = macro_context or {}
        geo_eval = mctx.get("geopolitical") or {}
        fund_eval = mctx.get("fundamental") or {}
        intermarket = mctx.get("intermarket") or {}
        hist_eval = mctx.get("historical_reactions") or {}

        if "geo_score" in geo_eval:
            geo_score = float(geo_eval["geo_score"])
        else:
            news_scores = [float(n.get("sentiment_score", 0.0) or 0.0) for n in news_articles]
            geo_score = sum(news_scores) / len(news_scores) if news_scores else 0.0

        # 3. Fundamental Score (-1.0 to 1.0) — Live Intermarket (DXY/US10Y) + Numeric Actual vs Forecast Surprises
        if "fund_score" in fund_eval:
            fund_score = float(fund_eval["fund_score"])
        else:
            fund_score = 0.0
            for event in economic_events:
                impact = str(event.get("sentiment_impact", "") or "").upper()
                if "BULLISH_GOLD" in impact or "BEARISH_USD" in impact:
                    fund_score += 0.22
                elif "BEARISH_GOLD" in impact or "BULLISH_USD" in impact:
                    fund_score -= 0.22
            fund_score = max(-1.0, min(1.0, fund_score))

        # Weighted 3-Pillar Composite Score (Technical 54% + Fundamental/Intermarket 26% + Geopolitical 20%)
        composite_score = (tech_score * 0.54) + (fund_score * 0.26) + (geo_score * 0.20)

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

        fund_notes_real = str(fund_eval.get("summary") or "").strip()
        hist_summary = str(hist_eval.get("summary") or "").strip()
        if fund_notes_real and hist_summary:
            final_fund_notes = f"{fund_notes_real} {hist_summary}"
        elif fund_notes_real:
            final_fund_notes = fund_notes_real
        else:
            final_fund_notes = (
                "Ekspektasi kebijakan suku bunga The Fed, imbal hasil Treasury AS, serta perbandingan "
                "Actual vs Forecast kalender ekonomi terdekat membentuk sentimen dasar XAU/USD."
            )

        geo_notes_real = str(geo_eval.get("summary") or "").strip()
        final_geo_notes = geo_notes_real if geo_notes_real else (
            "Dinamika geopolitik global dan aliran aset safe-haven tetap menjadi penopang volatilitas intraday emas."
        )

        if intermarket.get("market_regime_evidence"):
            sources.append(f"Intermarket Live: {intermarket['market_regime_evidence']}")

        return {
            "bias": bias,
            "confidence_score": confidence,
            "summary": summary,
            "fundamental_notes": final_fund_notes,
            "geopolitical_notes": final_geo_notes,
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
    def _build_entry_reasons(
        action: str,
        execution_type: str,
        entry_zone: str,
        entry_price: float,
        stop_loss: float,
        tp1: float,
        tp2: float,
        tp3: float,
        risk: float,
        reward1: float,
        reward2: float,
        reward3: float,
        rrr: str,
        session_name: str,
        confluence: Dict[str, Any],
        entry_source_detail: str = "",
        sl_source_detail: str = "",
        tp2_source_detail: str = "",
    ) -> List[Dict[str, str]]:
        """Builds 4 clear, easy-to-understand Indonesian reasons explaining WHY this Sniper setup was chosen."""
        align_label = str(confluence.get("alignment_label") or "M1–D1 MTF")
        htf = str(confluence.get("htf_bias") or "SIDEWAYS")
        itf = str(confluence.get("itf_bias") or "SIDEWAYS")
        ltf = str(confluence.get("ltf_bias") or "SIDEWAYS")

        risk_p = round(risk * 10.0)
        r1_p = round(reward1 * 10.0)
        r2_p = round(reward2 * 10.0)
        r3_p = round(reward3 * 10.0)
        rrr_tp1 = round(reward1 / risk, 1) if risk > 0 else 1.5

        if action == "WAIT":
            return [
                {
                    "title": "Perlindungan News",
                    "tag": "STANDBY",
                    "tone": "gold",
                    "detail": entry_source_detail or "Rilis berita ekonomi High-Impact segera berlangsung; spread & spike rawan menyapu SL ketat.",
                },
                {
                    "title": "Arah 7 Timeframe",
                    "tag": align_label.split("•")[0].strip(),
                    "tone": "gold",
                    "detail": f"Peta arah saat ini: HTF (D1/H4/H1) {htf}, ITF (M30/M15) {itf}, dan LTF (M5/M1) {ltf}.",
                },
                {
                    "title": "Rencana Sniper",
                    "tag": "SL 30–50p",
                    "tone": "cyan",
                    "detail": "Tunggu volatilitas mereda dan candle M5/M15 kembali tenang sebelum memasang entry sniper.",
                },
            ]

        dir_word = "naik (BUY)" if action == "BUY" else "turun (SELL)"
        dir_tone = "bullish" if action == "BUY" else "bearish"
        short_align = align_label.split("•")[0].strip()

        if htf == itf == ltf and htf in ("BULLISH", "BEARISH"):
            tf_detail = (
                f"Seluruh lapisan kompak {htf}: HTF (D1/H4/H1) {htf}, ITF (M30/M15) {itf}, "
                f"dan LTF (M5/M1) {ltf} — mendukung peluang {dir_word} berprobabilitas tinggi."
            )
        else:
            tf_detail = (
                f"Perbandingan 7 TF: HTF (D1/H4/H1) {htf}, ITF (M30/M15) {itf}, LTF (M5/M1) {ltf}. "
                f"Eksekusi {dir_word} mengikuti dominasi arus dan momentum intraday terbaru."
            )

        if execution_type == "INSTANT":
            entry_tag = "SNIPER NOW"
            default_entry_detail = (
                f"Harga berada tepat di dekat struktur/EMA aktif dengan konfirmasi candle M1/M5 — "
                f"siap eksekusi di {entry_zone} tanpa perlu mengejar harga."
            )
        else:
            entry_tag = "SNIPER LIMIT"
            default_entry_detail = (
                f"Anti-kejar harga: menunggu retest/pullback tipis ke zona {entry_zone} agar posisi masuk "
                f"sedekat mungkin dengan batas struktur dan SL ketat tetap terlindungi."
            )

        sl_side = "di bawah" if action == "BUY" else "di atas"
        default_sl_detail = (
            f"SL ditaruh di ${stop_loss:.2f} (-{risk_p:.0f} pips) {sl_side} struktur swing terdekat — "
            f"terjaga ketat di profil 30–50 pips sesuai volatilitas {session_name}."
        )

        tp2_hint = f" • {tp2_source_detail}" if tp2_source_detail else " • struktur M15/H1"
        tp_detail = (
            f"TP1 dikunci tepat +{r1_p:.0f} pips di ${tp1:.2f} (40% lot, RRR 1:{rrr_tp1} → langsung geser SL ke BEP). "
            f"TP2 ${tp2:.2f} (+{r2_p:.0f}p{tp2_hint}, 40% lot → SL ke TP1) & TP3 ${tp3:.2f} (+{r3_p:.0f}p, 20% runner)."
        )

        return [
            {"title": "Arah 7 Timeframe", "tag": short_align, "tone": dir_tone, "detail": tf_detail},
            {"title": "Alasan Zona Entry", "tag": entry_tag, "tone": "cyan", "detail": entry_source_detail or default_entry_detail},
            {"title": "Proteksi SL Ketat", "tag": f"-{risk_p:.0f} pips", "tone": "bearish", "detail": sl_source_detail or default_sl_detail},
            {"title": "Target TP1–TP3", "tag": f"TP1 +{r1_p:.0f}p • {rrr}", "tone": "bullish", "detail": tp_detail},
        ]

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
        7-Timeframe Confluence & Sniper Scalping Engine:
        - Strict Sniper SL: 30–50 pips ($3.00–$5.00) behind nearest structural swing (anti-chase Limit when far).
        - Strict TP1: 60 pips ($6.00) for 40% lock + SL->BEP (RRR 1:1.2 to 1:2.0 at TP1 alone).
        - Adaptive TP2 & TP3: Snaps to next M15/M30/H1/H4 structural/confluence targets.
        - Transparent 4-point `entry_reasons` explaining every level clearly.
        """
        mtf = mtf_technical or {}
        m1 = mtf.get("1m") or m5_data or technical_data
        m5 = m5_data or mtf.get("5m") or technical_data
        m15 = m15_data or mtf.get("15m") or technical_data
        m30 = mtf.get("30m") or m15
        h1 = mtf.get("1h") or technical_data
        h4 = mtf.get("4h") or h1
        confluence = mtf.get("confluence") or {}
        conf_sups = confluence.get("confluence_supports") or []
        conf_ress = confluence.get("confluence_resistances") or []
        align_label = str(confluence.get("alignment_label") or "MTF 7-TF")
        conf_note = str(confluence.get("confluence_note") or "")
        mtf_overview = confluence.get("overview") or []

        atr_m15 = float(m15.get("atr_14") or technical_data.get("atr_14") or 3.50)
        atr_m5 = float(m5.get("atr_14") or (atr_m15 * 0.65))
        session_name = str(m15.get("session_name") or "Global Session")
        session_vol = str(m15.get("session_volatility") or "MEDIUM")

        # Strict Sniper SL calibration: 30–50 pips ($3.00–$5.00) adaptive to session volatility
        if session_vol in ("HIGH", "MEDIUM_HIGH"):
            base_risk = round(max(3.80, min(5.00, 3.40 + atr_m5 * 0.14)), 2)
        else:
            base_risk = round(max(3.00, min(4.00, 2.85 + atr_m5 * 0.10)), 2)

        # Check for imminent high-impact news blackout (< 15 min)
        imminent_event = AIAgentEngine._has_imminent_high_impact_event(economic_events or [], minutes_window=15)
        if imminent_event:
            valid_sups = sorted([s for s in supports if s < curr_price], reverse=True)
            valid_res = sorted([r for r in resistances if r > curr_price])
            p_sup = valid_sups[0] if valid_sups else round(curr_price - base_risk, 2)
            p_res = valid_res[0] if valid_res else round(curr_price + base_risk, 2)
            sl = round(curr_price - base_risk, 2)
            tp1 = round(curr_price + 6.00, 2)
            tp2 = round(curr_price + 10.50, 2)
            tp3 = round(curr_price + 16.50, 2)
            reasons = AIAgentEngine._build_entry_reasons(
                action="WAIT",
                execution_type="WAIT",
                entry_zone=f"Tunggu rilis {imminent_event}",
                entry_price=round(curr_price, 2),
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                tp3=tp3,
                risk=base_risk,
                reward1=6.00,
                reward2=10.50,
                reward3=16.50,
                rrr=f"1 : {round(16.50 / base_risk, 1)}",
                session_name=session_name,
                confluence=confluence,
                entry_source_detail=(
                    f"News Guard aktif: rilis High-Impact '{imminent_event}' dalam <15 menit. "
                    f"Hindari whipsaw spread; pantau struktur di sekitar ${p_sup:.2f}–${p_res:.2f} setelah rilis."
                ),
            )
            return {
                "action": "WAIT",
                "action_label": "WAIT • NEWS GUARD (<15m)",
                "execution_type": "WAIT",
                "scalp_timeframe": "M1–D1 MTF",
                "session_name": session_name,
                "atr_pips": round(atr_m15 * 10.0, 1),
                "mtf_alignment": align_label,
                "mtf_overview": mtf_overview,
                "confluence_note": conf_note,
                "setup_quality_score": 60,
                "zone_proof": f"News Guard Aktif (<15m jelang {imminent_event})",
                "zone_distance_pips": 0.0,
                "entry_zone": f"Tunggu rilis {imminent_event} selesai",
                "entry_price": round(curr_price, 2),
                "stop_loss": sl,
                "take_profit_1": tp1,
                "take_profit_2": tp2,
                "take_profit_3": tp3,
                "risk_reward_ratio": f"1 : {round(16.50 / base_risk, 1)}",
                "risk_pips": round(base_risk * 10.0, 1),
                "reward_tp1_pips": 60.0,
                "reward_tp2_pips": 105.0,
                "reward_tp3_pips": 165.0,
                "lot_management": "Tahan entry sementara hingga lonjakan spread news mereda",
                "entry_reasons": reasons,
                "technical_rationale": (
                    f"Perlindungan News Guard aktif: rilis High-Impact '{imminent_event}' berlangsung dalam <15 menit. "
                    f"Hindari whipsaw spread; pantau breakout valid di atas ${p_res:.2f} atau breakdown di bawah ${p_sup:.2f}."
                ),
                "invalidation_level": "Lonjakan spread ekstrem menjelang rilis data High-Impact.",
                "status": "ACTIVE",
                "status_message": f"News Guard Aktif — Tunggu rilis {imminent_event}",
            }

        # Gather structural target levels across all 7 timeframes (for TP2 & TP3)
        target_sups_raw: List[tuple[float, str]] = []
        target_ress_raw: List[tuple[float, str]] = []
        for c in conf_sups:
            target_sups_raw.append((round(float(c["price"]), 2), f"Demand {'+'.join(c['timeframes'][:4])}"))
        for c in conf_ress:
            target_ress_raw.append((round(float(c["price"]), 2), f"Supply {'+'.join(c['timeframes'][:4])}"))
        for tf_lbl, td in (("M5", m5), ("M15", m15), ("M30", m30), ("H1", h1), ("H4", h4)):
            for lv in (td.get("support_levels") or []) + (td.get("swing_lows") or []):
                target_sups_raw.append((round(float(lv), 2), f"support {tf_lbl}"))
            for lv in (td.get("resistance_levels") or []) + (td.get("swing_highs") or []):
                target_ress_raw.append((round(float(lv), 2), f"resistance {tf_lbl}"))

        def _pick_proven_key_zone(
            zones: List[Dict[str, Any]],
            is_supply: bool,
        ) -> tuple[Optional[Dict[str, Any]], bool]:
            """
            Selects an authentic proven Key Structural Zone (Supply/Demand/Flip):
            1. Checks if price is ALREADY right inside a high-conviction multi-TF wall (<= 18p) for INSTANT sniper.
            2. Otherwise strictly avoids noisy near-spot levels (< 45p) and selects the highest-quality
               structural wall at a safe distance (45 - 450 pips from current spot).
            """
            # Check active retest of a major proven wall right now (<= 18p away)
            active_wall = next(
                (
                    z for z in zones
                    if float(z.get("distance_pips", 999)) <= 18.0
                    and int(z.get("htf_itf_count", 0)) >= 2
                    and int(z.get("rejections", 0)) >= 2
                ),
                None,
            )
            if active_wall is not None:
                return active_wall, True

            # Primary choice: Safe-distance proven Key Zone (45 - 450 pips away, NOT too close to spot!)
            safe_zones = [
                z for z in zones
                if 45.0 <= float(z.get("distance_pips", 0)) <= 450.0
                and (int(z.get("htf_itf_count", 0)) >= 1 or int(z.get("touches", 0)) >= 2)
            ]
            if safe_zones:
                # Prefer strong multi-TF / high-quality zones; among equally strong zones prefer reachable ones
                safe_zones.sort(
                    key=lambda z: (
                        int(z.get("quality_score", 70))
                        + (6 if int(z.get("htf_itf_count", 0)) >= 2 else 0)
                        + (4 if 60.0 <= float(z.get("distance_pips", 0)) <= 360.0 else 0)
                    ),
                    reverse=True,
                )
                return safe_zones[0], False

            # Secondary fallback: any structural zone >= 40 pips away
            wider = [z for z in zones if float(z.get("distance_pips", 0)) >= 40.0]
            if wider:
                return wider[0], False

            return None, False

        if bias == "BULLISH":
            action = "BUY"
            m1_pa = str(m1.get("price_action", "")).upper()
            m5_pa = str(m5.get("price_action", "")).upper()
            pa_bull = m1_pa.startswith("BULLISH") or m5_pa.startswith("BULLISH")

            picked_zone, is_at_wall = _pick_proven_key_zone(conf_sups, is_supply=False)

            if picked_zone is not None and is_at_wall and pa_bull:
                execution_type = "INSTANT"
                action_label = "BUY NOW (KEY ZONE)"
                entry_price = round(curr_price, 2)
                z_low = round(min(float(picked_zone["low"]), entry_price - 0.55), 2)
                z_high = round(max(float(picked_zone["high"]), entry_price + 0.55), 2)
                # Keep tight pocket around current wall touch
                entry_low = round(max(entry_price - 0.85, z_low), 2)
                entry_high = round(min(entry_price + 0.85, z_high), 2)
                zone_proof = str(picked_zone.get("proof_text") or "Retest Key Demand MTF aktif")
                setup_quality = int(picked_zone.get("quality_score", 82))
                zone_dist_pips = round(abs(entry_price - curr_price) * 10.0, 1)
                entry_src_detail = (
                    f"Harga sedang menyentuh langsung tembok Key Demand (${entry_price:.2f}) dengan konfirmasi buyer M1/M5. "
                    f"Bukti: {zone_proof}."
                )
            elif picked_zone is not None:
                execution_type = "LIMIT"
                action_label = "BUY LIMIT (KEY ZONE)"
                entry_price = round(float(picked_zone["price"]), 2)
                entry_low = round(float(picked_zone["low"]), 2)
                entry_high = round(float(picked_zone["high"]), 2)
                if (entry_high - entry_low) < 0.90:
                    entry_low = round(entry_price - 0.60, 2)
                    entry_high = round(entry_price + 0.60, 2)
                zone_proof = str(picked_zone.get("proof_text") or "Zona Demand struktural terkonfirmasi")
                setup_quality = int(picked_zone.get("quality_score", 80))
                zone_dist_pips = round(abs(curr_price - entry_price) * 10.0, 1)
                entry_src_detail = (
                    f"Sabar menunggu pullback -{zone_dist_pips:.0f} pips ke Key Demand asli (${entry_price:.2f}) — "
                    f"menghindari zona terlalu dekat spot yang rawan sapuan. Bukti: {zone_proof}."
                )
            else:
                # Safe structural pullback >= 55 pips below spot if no higher-TF zone was in list
                execution_type = "LIMIT"
                action_label = "BUY LIMIT (KEY ZONE)"
                deep_sups = sorted([lv for lv, _ in target_sups_raw if (curr_price - lv) >= 4.50], reverse=True)
                entry_price = round(deep_sups[0], 2) if deep_sups else round(curr_price - max(6.00, atr_m15 * 0.8), 2)
                entry_low = round(entry_price - 0.65, 2)
                entry_high = round(entry_price + 0.65, 2)
                zone_dist_pips = round(abs(curr_price - entry_price) * 10.0, 1)
                zone_proof = f"Area Demand struktural M15/H1 (-{zone_dist_pips:.0f} pips di bawah harga spot)"
                setup_quality = 74
                entry_src_detail = (
                    f"Menghindari entry di area tanggung/terlalu dekat spot: pasang BUY LIMIT di area Demand "
                    f"${entry_price:.2f} (-{zone_dist_pips:.0f} pips) agar rasio risk-reward optimal."
                )

            entry_zone = f"${entry_low:.2f} - ${entry_high:.2f}"

            # Strict Sniper SL: 30–50 pips ($3.00–$5.00) cleanly outside the lower wall edge
            wall_sl = round(entry_low - max(2.40, base_risk - (entry_price - entry_low)), 2)
            dist_wall = round(entry_price - wall_sl, 2)
            if dist_wall < 3.00:
                stop_loss = round(entry_price - 3.20, 2)
            elif dist_wall > 5.00:
                stop_loss = round(entry_price - 5.00, 2)
            else:
                stop_loss = wall_sl
            if stop_loss >= entry_low - 1.20:
                stop_loss = round(min(entry_low - 2.00, entry_price - base_risk), 2)
            risk = round(entry_price - stop_loss, 2)
            if risk < 3.00:
                stop_loss = round(entry_price - 3.00, 2)
                risk = 3.00
            elif risk > 5.00:
                stop_loss = round(entry_price - 5.00, 2)
                risk = 5.00

            sl_src_detail = (
                f"SL di ${stop_loss:.2f} (-{round(risk * 10):.0f} pips) diletakkan persis di bawah ekor zona Demand "
                f"(${entry_low:.2f}) — terlindungi tembok struktur & tetap ketat di profil 30–50 pips."
            )

            # Strict TP1: exactly +60 pips ($6.00) -> 40% lot lock & SL->BEP
            tp1 = round(entry_price + 6.00, 2)

            # Adaptive TP2: aim at real opposing Supply/Resistance ahead (at least +100p, up to +260p)
            tp2_match = next(
                (
                    (round(lv - 0.50, 2), lbl)
                    for lv, lbl in sorted(target_ress_raw, key=lambda x: x[0])
                    if (entry_price + 9.50) <= (lv - 0.50) <= (entry_price + 26.00)
                ),
                None,
            )
            if tp2_match:
                tp2, tp2_src = tp2_match
            else:
                tp2 = round(entry_price + max(11.00, min(16.00, risk * 3.00)), 2)
                tp2_src = "proyeksi struktur M15/H1"

            # Adaptive TP3 (Runner): aim at next major Supply/Resistance wall
            tp3_match = next(
                (
                    (round(lv - 0.60, 2), lbl)
                    for lv, lbl in sorted(target_ress_raw, key=lambda x: x[0])
                    if (tp2 + 4.50) <= (lv - 0.60) <= (entry_price + 38.00)
                ),
                None,
            )
            if tp3_match:
                tp3 = tp3_match[0]
            else:
                tp3 = round(max(tp2 + 5.50, entry_price + max(17.00, risk * 4.20)), 2)

            reward1 = round(tp1 - entry_price, 2)
            reward2 = round(tp2 - entry_price, 2)
            reward3 = round(tp3 - entry_price, 2)
            rrr = f"1 : {round(reward3 / risk, 1)}" if risk > 0 else "1 : 4.2"

            entry_reasons = AIAgentEngine._build_entry_reasons(
                action=action,
                execution_type=execution_type,
                entry_zone=entry_zone,
                entry_price=entry_price,
                stop_loss=stop_loss,
                tp1=tp1,
                tp2=tp2,
                tp3=tp3,
                risk=risk,
                reward1=reward1,
                reward2=reward2,
                reward3=reward3,
                rrr=rrr,
                session_name=session_name,
                confluence=confluence,
                entry_source_detail=entry_src_detail,
                sl_source_detail=sl_src_detail,
                tp2_source_detail=tp2_src,
            )
            rationale = (
                f"Key-Zone BUY ({align_label}, Kualitas {setup_quality}/100): {entry_src_detail} "
                f"SL ketat ${stop_loss:.2f} (-{round(risk * 10):.0f}p), "
                f"TP1 ${tp1:.2f} (+{round(reward1 * 10):.0f}p, 40% & BEP), "
                f"TP2 ${tp2:.2f} (+{round(reward2 * 10):.0f}p), TP3 ${tp3:.2f} (+{round(reward3 * 10):.0f}p)."
            )
            invalidation = f"Close candle M15 di bawah ${stop_loss:.2f} menembus zona Demand dan membatalkan setup BUY."

        else:
            action = "SELL"
            m1_pa = str(m1.get("price_action", "")).upper()
            m5_pa = str(m5.get("price_action", "")).upper()
            pa_bear = m1_pa.startswith("BEARISH") or m5_pa.startswith("BEARISH")

            picked_zone, is_at_wall = _pick_proven_key_zone(conf_ress, is_supply=True)

            if picked_zone is not None and is_at_wall and pa_bear:
                execution_type = "INSTANT"
                action_label = "SELL NOW (KEY ZONE)"
                entry_price = round(curr_price, 2)
                z_low = round(min(float(picked_zone["low"]), entry_price - 0.55), 2)
                z_high = round(max(float(picked_zone["high"]), entry_price + 0.55), 2)
                entry_low = round(max(entry_price - 0.85, z_low), 2)
                entry_high = round(min(entry_price + 0.85, z_high), 2)
                zone_proof = str(picked_zone.get("proof_text") or "Retest Key Supply MTF aktif")
                setup_quality = int(picked_zone.get("quality_score", 82))
                zone_dist_pips = round(abs(entry_price - curr_price) * 10.0, 1)
                entry_src_detail = (
                    f"Harga sedang menyentuh langsung tembok Key Supply (${entry_price:.2f}) dengan konfirmasi seller M1/M5. "
                    f"Bukti: {zone_proof}."
                )
            elif picked_zone is not None:
                execution_type = "LIMIT"
                action_label = "SELL LIMIT (KEY ZONE)"
                entry_price = round(float(picked_zone["price"]), 2)
                entry_low = round(float(picked_zone["low"]), 2)
                entry_high = round(float(picked_zone["high"]), 2)
                if (entry_high - entry_low) < 0.90:
                    entry_low = round(entry_price - 0.60, 2)
                    entry_high = round(entry_price + 0.60, 2)
                zone_proof = str(picked_zone.get("proof_text") or "Zona Supply struktural terkonfirmasi")
                setup_quality = int(picked_zone.get("quality_score", 80))
                zone_dist_pips = round(abs(entry_price - curr_price) * 10.0, 1)
                entry_src_detail = (
                    f"Sabar menunggu pullback +{zone_dist_pips:.0f} pips ke Key Supply asli (${entry_price:.2f}) — "
                    f"menghindari jual di area terlalu dekat/rawan sweep. Bukti: {zone_proof}."
                )
            else:
                execution_type = "LIMIT"
                action_label = "SELL LIMIT (KEY ZONE)"
                deep_res = sorted([lv for lv, _ in target_ress_raw if (lv - curr_price) >= 4.50])
                entry_price = round(deep_res[0], 2) if deep_res else round(curr_price + max(6.00, atr_m15 * 0.8), 2)
                entry_low = round(entry_price - 0.65, 2)
                entry_high = round(entry_price + 0.65, 2)
                zone_dist_pips = round(abs(entry_price - curr_price) * 10.0, 1)
                zone_proof = f"Area Supply struktural M15/H1 (+{zone_dist_pips:.0f} pips di atas harga spot)"
                setup_quality = 74
                entry_src_detail = (
                    f"Menghindari entry di area tanggung/terlalu dekat spot: pasang SELL LIMIT di area Supply "
                    f"${entry_price:.2f} (+{zone_dist_pips:.0f} pips) agar rasio risk-reward optimal."
                )

            entry_zone = f"${entry_low:.2f} - ${entry_high:.2f}"

            # Strict Sniper SL: 30–50 pips ($3.00–$5.00) cleanly outside the upper wall edge
            wall_sl = round(entry_high + max(2.40, base_risk - (entry_high - entry_price)), 2)
            dist_wall = round(wall_sl - entry_price, 2)
            if dist_wall < 3.00:
                stop_loss = round(entry_price + 3.20, 2)
            elif dist_wall > 5.00:
                stop_loss = round(entry_price + 5.00, 2)
            else:
                stop_loss = wall_sl
            if stop_loss <= entry_high + 1.20:
                stop_loss = round(max(entry_high + 2.00, entry_price + base_risk), 2)
            risk = round(stop_loss - entry_price, 2)
            if risk < 3.00:
                stop_loss = round(entry_price + 3.00, 2)
                risk = 3.00
            elif risk > 5.00:
                stop_loss = round(entry_price + 5.00, 2)
                risk = 5.00

            sl_src_detail = (
                f"SL di ${stop_loss:.2f} (-{round(risk * 10):.0f} pips) diletakkan persis di atas ekor zona Supply "
                f"(${entry_high:.2f}) — terlindungi tembok struktur & tetap ketat di profil 30–50 pips."
            )

            # Strict TP1: exactly +60 pips ($6.00) -> 40% lot lock & SL->BEP
            tp1 = round(entry_price - 6.00, 2)

            # Adaptive TP2: aim at real opposing Demand/Support below (at least +95p, up to +260p)
            tp2_match = next(
                (
                    (round(lv + 0.50, 2), lbl)
                    for lv, lbl in sorted(target_sups_raw, key=lambda x: x[0], reverse=True)
                    if (entry_price - 26.00) <= (lv + 0.50) <= (entry_price - 9.50)
                ),
                None,
            )
            if tp2_match:
                tp2, tp2_src = tp2_match
            else:
                tp2 = round(entry_price - max(11.00, min(16.00, risk * 3.00)), 2)
                tp2_src = "proyeksi struktur M15/H1"

            # Adaptive TP3 (Runner): aim at next major Demand/Support wall below TP2
            tp3_match = next(
                (
                    (round(lv + 0.60, 2), lbl)
                    for lv, lbl in sorted(target_sups_raw, key=lambda x: x[0], reverse=True)
                    if (entry_price - 38.00) <= (lv + 0.60) <= (tp2 - 4.50)
                ),
                None,
            )
            if tp3_match:
                tp3 = tp3_match[0]
            else:
                tp3 = round(min(tp2 - 5.50, entry_price - max(17.00, risk * 4.20)), 2)

            reward1 = round(entry_price - tp1, 2)
            reward2 = round(entry_price - tp2, 2)
            reward3 = round(entry_price - tp3, 2)
            rrr = f"1 : {round(reward3 / risk, 1)}" if risk > 0 else "1 : 4.2"

            entry_reasons = AIAgentEngine._build_entry_reasons(
                action=action,
                execution_type=execution_type,
                entry_zone=entry_zone,
                entry_price=entry_price,
                stop_loss=stop_loss,
                tp1=tp1,
                tp2=tp2,
                tp3=tp3,
                risk=risk,
                reward1=reward1,
                reward2=reward2,
                reward3=reward3,
                rrr=rrr,
                session_name=session_name,
                confluence=confluence,
                entry_source_detail=entry_src_detail,
                sl_source_detail=sl_src_detail,
                tp2_source_detail=tp2_src,
            )
            rationale = (
                f"Key-Zone SELL ({align_label}, Kualitas {setup_quality}/100): {entry_src_detail} "
                f"SL ketat ${stop_loss:.2f} (-{round(risk * 10):.0f}p), "
                f"TP1 ${tp1:.2f} (+{round(reward1 * 10):.0f}p, 40% & BEP), "
                f"TP2 ${tp2:.2f} (+{round(reward2 * 10):.0f}p), TP3 ${tp3:.2f} (+{round(reward3 * 10):.0f}p)."
            )
            invalidation = f"Close candle M15 di atas ${stop_loss:.2f} menembus zona Supply dan membatalkan setup SELL."

        if execution_type == "INSTANT":
            action_hint = f"Harga tepat di Key Zone ${entry_price:.2f} — siap eksekusi (SL -{round(risk * 10):.0f}p)"
            initial_status = "ACTIVE"
        else:
            verb = "turun" if action == "BUY" else "naik"
            sign = "-" if action == "BUY" else "+"
            action_hint = (
                f"Menunggu harga {verb} {sign}{zone_dist_pips:.0f} pips ke Key Zone {entry_zone} "
                f"(SL -{round(risk * 10):.0f}p aman di luar tembok)"
            )
            initial_status = "PENDING_LIMIT"

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
            "setup_quality_score": setup_quality,
            "zone_proof": zone_proof,
            "zone_distance_pips": zone_dist_pips,
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
            "lot_management": "40% TP1 +60p (SL→BEP) • 40% TP2 (SL→TP1) • 20% Runner TP3",
            "entry_reasons": entry_reasons,
            "technical_rationale": rationale,
            "invalidation_level": invalidation,
            "status": initial_status,
            "status_message": action_hint,
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

        # Preserve proven Key Zone LIMIT entries up to $48.00 (480 pips) away from live spot!
        execution_type = str(raw_setup.get("execution_type", "")).strip().upper()
        try:
            entry_p = round(float(raw_setup.get("entry_price", curr_price)), 2)
        except (ValueError, TypeError):
            entry_p = round(curr_price, 2)

        if entry_p <= 0 or abs(entry_p - curr_price) > 48.00:
            entry_p = round(curr_price, 2)
        # Ensure directional validity for pending Limit orders (BUY LIMIT <= spot, SELL LIMIT >= spot)
        if execution_type == "LIMIT":
            if action == "BUY" and entry_p > curr_price + 0.50:
                entry_p = round(curr_price - 5.50, 2)
            elif action == "SELL" and entry_p < curr_price - 0.50:
                entry_p = round(curr_price + 5.50, 2)

        if execution_type not in ["INSTANT", "LIMIT", "WAIT"]:
            if action == "WAIT":
                execution_type = "WAIT"
            else:
                execution_type = "INSTANT" if abs(entry_p - curr_price) <= 1.20 else "LIMIT"

        # Tight Sniper scalping profile: SL strictly 30–50 pips ($3.00–$5.00), TP1 60 pips ($6.00)
        session_vol = str(m15.get("session_volatility") or (technical_data or {}).get("session_volatility") or "MEDIUM")
        atr_m5 = float((m5_data or {}).get("atr_14") or (atr_m15 * 0.65))
        if session_vol in ("HIGH", "MEDIUM_HIGH"):
            default_risk = round(max(3.80, min(5.00, 3.40 + atr_m5 * 0.14)), 2)
        else:
            default_risk = round(max(3.00, min(4.00, 2.85 + atr_m5 * 0.10)), 2)
        half_zone = round(max(0.60, min(0.90, default_risk * 0.18)), 2)
        min_risk = 3.00
        max_risk = 5.00

        def safe_float(val: Any) -> float:
            try:
                return round(float(val), 2)
            except (ValueError, TypeError):
                return 0.0

        ai_rationale = str(raw_setup.get("technical_rationale", "")).strip()
        ai_invalidation = str(raw_setup.get("invalidation_level", "")).strip()
        lot_mgmt = str(raw_setup.get("lot_management", "")).strip() or "40% TP1 +60p (SL→BEP) • 40% TP2 (SL→TP1) • 20% Runner TP3"
        scalp_tf = str(raw_setup.get("scalp_timeframe", "")).strip() or "M1–D1 MTF"
        confluence = (mtf_technical or {}).get("confluence") or {}
        mtf_overview = confluence.get("overview") or raw_setup.get("mtf_overview") or []
        mtf_alignment = str(confluence.get("alignment_label") or raw_setup.get("mtf_alignment") or "M1–D1 MTF")
        confluence_note = str(raw_setup.get("confluence_note") or confluence.get("confluence_note") or "").strip()

        # Preserve or compute setup_quality_score, zone_proof & zone_distance_pips
        conf_sups = confluence.get("confluence_supports") or []
        conf_ress = confluence.get("confluence_resistances") or []
        matched_zone_pool = conf_sups if action == "BUY" else conf_ress
        nearest_proven = next(
            (z for z in matched_zone_pool if abs(float(z.get("price", 0)) - entry_p) <= 3.50),
            matched_zone_pool[0] if matched_zone_pool else None,
        )
        try:
            setup_quality = int(raw_setup.get("setup_quality_score") or (nearest_proven.get("quality_score") if nearest_proven else 78))
        except (ValueError, TypeError):
            setup_quality = 78
        setup_quality = max(55, min(96, setup_quality))
        zone_proof = str(raw_setup.get("zone_proof") or (nearest_proven.get("proof_text") if nearest_proven else "")).strip()
        zone_dist_pips = round(abs(entry_p - curr_price) * 10.0, 1)
        if not zone_proof:
            side_lbl = "Demand" if action == "BUY" else "Supply"
            zone_proof = f"Zona {side_lbl} struktural MTF ({zone_dist_pips:.0f} pips dari spot)"

        # Parse custom entry_zone bounds if valid and consistent with entry_p
        raw_ez = str(raw_setup.get("entry_zone", "")).strip()
        entry_low = round(entry_p - half_zone, 2)
        entry_high = round(entry_p + half_zone, 2)
        if "-" in raw_ez and "$" in raw_ez:
            try:
                parts = [float(p.replace("$", "").strip()) for p in raw_ez.split("-")[:2]]
                if len(parts) == 2 and parts[0] < parts[1] and (parts[1] - parts[0]) <= 2.60 and abs(((parts[0] + parts[1]) / 2.0) - entry_p) <= 0.80:
                    entry_low = round(parts[0], 2)
                    entry_high = round(parts[1], 2)
            except Exception:
                pass

        if action == "BUY":
            entry_price = entry_p
            entry_zone = f"${entry_low:.2f} - ${entry_high:.2f}"
            action_label = str(raw_setup.get("action_label", "")).strip() or (
                "BUY NOW (KEY ZONE)" if execution_type == "INSTANT" else "BUY LIMIT (KEY ZONE)"
            )

            sl = safe_float(raw_setup.get("stop_loss"))
            if sl <= 0 or sl >= entry_low or (entry_price - sl) < min_risk or (entry_price - sl) > max_risk:
                sl = round(entry_price - default_risk, 2)
            risk = round(entry_price - sl, 2)

            # Strict TP1: 60 pips ($6.00; preserve AI within $5.80..$6.20, otherwise snap to exact $6.00)
            tp1 = safe_float(raw_setup.get("take_profit_1"))
            if tp1 <= entry_high or not (5.80 <= (tp1 - entry_price) <= 6.20):
                tp1 = round(entry_price + 6.00, 2)

            # Wide structural ceiling for Key-Zone TP2 & TP3 (up to 320p / 450p!)
            tp2 = safe_float(raw_setup.get("take_profit_2"))
            if tp2 < (tp1 + 3.00) or (tp2 - entry_price) > 32.00:
                tp2 = round(entry_price + max(11.00, min(16.00, risk * 3.00)), 2)

            tp3 = safe_float(raw_setup.get("take_profit_3"))
            if tp3 < (tp2 + 4.00) or (tp3 - entry_price) > 45.00:
                tp3 = round(max(tp2 + 5.50, entry_price + max(17.00, risk * 4.20)), 2)

            reward1 = round(tp1 - entry_price, 2)
            reward2 = round(tp2 - entry_price, 2)
            reward3 = round(tp3 - entry_price, 2)
            rrr = f"1 : {round(reward3 / risk, 1)}" if risk > 0 else "1 : 4.2"

            rationale = ai_rationale if len(ai_rationale) >= 25 else (
                f"Setup Key-Zone BUY ({session_name}, Kualitas {setup_quality}/100): Entry {entry_zone}, SL ketat ${sl:.2f} (-{round(risk * 10):.0f} pips). "
                f"Amankan 40% di TP1 ${tp1:.2f} (+{round(reward1 * 10):.0f}p, SL→BEP), "
                f"40% di TP2 ${tp2:.2f} (+{round(reward2 * 10):.0f}p, SL→TP1), "
                f"dan 20% runner menuju TP3 ${tp3:.2f} (+{round(reward3 * 10):.0f}p)."
            )
            invalidation = ai_invalidation if len(ai_invalidation) >= 12 else (
                f"Close candle M15 di bawah ${sl:.2f} menembus zona Demand dan membatalkan setup BUY."
            )

        elif action == "SELL":
            entry_price = entry_p
            entry_zone = f"${entry_low:.2f} - ${entry_high:.2f}"
            action_label = str(raw_setup.get("action_label", "")).strip() or (
                "SELL NOW (KEY ZONE)" if execution_type == "INSTANT" else "SELL LIMIT (KEY ZONE)"
            )

            sl = safe_float(raw_setup.get("stop_loss"))
            if sl <= 0 or sl <= entry_high or (sl - entry_price) < min_risk or (sl - entry_price) > max_risk:
                sl = round(entry_price + default_risk, 2)
            risk = round(sl - entry_price, 2)

            tp1 = safe_float(raw_setup.get("take_profit_1"))
            if tp1 <= 0 or tp1 >= entry_low or not (5.80 <= (entry_price - tp1) <= 6.20):
                tp1 = round(entry_price - 6.00, 2)

            tp2 = safe_float(raw_setup.get("take_profit_2"))
            if tp2 <= 0 or tp2 > (tp1 - 3.00) or (entry_price - tp2) > 32.00:
                tp2 = round(entry_price - max(11.00, min(16.00, risk * 3.00)), 2)

            tp3 = safe_float(raw_setup.get("take_profit_3"))
            if tp3 <= 0 or tp3 > (tp2 - 4.00) or (entry_price - tp3) > 45.00:
                tp3 = round(min(tp2 - 5.50, entry_price - max(17.00, risk * 4.20)), 2)

            reward1 = round(entry_price - tp1, 2)
            reward2 = round(entry_price - tp2, 2)
            reward3 = round(entry_price - tp3, 2)
            rrr = f"1 : {round(reward3 / risk, 1)}" if risk > 0 else "1 : 4.2"

            rationale = ai_rationale if len(ai_rationale) >= 25 else (
                f"Setup Key-Zone SELL ({session_name}, Kualitas {setup_quality}/100): Entry {entry_zone}, SL ketat ${sl:.2f} (-{round(risk * 10):.0f} pips). "
                f"Amankan 40% di TP1 ${tp1:.2f} (+{round(reward1 * 10):.0f}p, SL→BEP), "
                f"40% di TP2 ${tp2:.2f} (+{round(reward2 * 10):.0f}p, SL→TP1), "
                f"dan 20% runner menuju TP3 ${tp3:.2f} (+{round(reward3 * 10):.0f}p)."
            )
            invalidation = ai_invalidation if len(ai_invalidation) >= 12 else (
                f"Close candle M15 di atas ${sl:.2f} menembus zona Supply dan membatalkan setup SELL."
            )

        else:
            action = "WAIT"
            execution_type = "WAIT"
            action_label = str(raw_setup.get("action_label", "")).strip() or "WAIT • NEWS GUARD"
            entry_price = round(curr_price, 2)
            entry_zone = str(raw_setup.get("entry_zone", "")).strip() or f"Breakout > ${primary_res:.2f} / < ${primary_sup:.2f}"
            sl = round(entry_price - default_risk, 2)
            tp1 = round(entry_price + 6.00, 2)
            tp2 = round(entry_price + 11.00, 2)
            tp3 = round(entry_price + 17.00, 2)
            risk = default_risk
            reward1 = round(tp1 - entry_price, 2)
            reward2 = round(tp2 - entry_price, 2)
            reward3 = round(tp3 - entry_price, 2)
            rrr = f"1 : {round(reward3 / risk, 1)}" if risk > 0 else "1 : 4.2"
            rationale = ai_rationale if len(ai_rationale) >= 20 else (
                f"Menunggu konfirmasi breakout dari area ${primary_sup:.2f}–${primary_res:.2f} agar terhindar dari whipsaw."
            )
            invalidation = ai_invalidation if len(ai_invalidation) >= 10 else "Lonjakan spread & whipsaw news."

        # Normalize structured entry_reasons (preserve AI's 4 bullets when valid, else auto-build clean reasons)
        raw_reasons = raw_setup.get("entry_reasons")
        entry_reasons: List[Dict[str, str]] = []
        if isinstance(raw_reasons, list):
            for item in raw_reasons:
                if isinstance(item, dict) and str(item.get("title", "")).strip() and str(item.get("detail", "")).strip():
                    entry_reasons.append({
                        "title": str(item.get("title", "")).strip(),
                        "tag": str(item.get("tag", "")).strip(),
                        "tone": str(item.get("tone", "gold")).strip().lower(),
                        "detail": str(item.get("detail", "")).strip(),
                    })
        if len(entry_reasons) < 3:
            entry_reasons = AIAgentEngine._build_entry_reasons(
                action=action,
                execution_type=execution_type,
                entry_zone=entry_zone,
                entry_price=entry_price,
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                tp3=tp3,
                risk=risk,
                reward1=reward1,
                reward2=reward2,
                reward3=reward3,
                rrr=rrr,
                session_name=session_name,
                confluence=confluence,
            )

        if execution_type == "INSTANT":
            action_hint = f"Harga tepat di Key Zone ${entry_price:.2f} — siap eksekusi (SL -{round(risk * 10):.0f}p)"
            init_status = "ACTIVE"
        elif execution_type == "LIMIT":
            verb = "turun" if action == "BUY" else "naik"
            sign = "-" if action == "BUY" else "+"
            action_hint = (
                f"Menunggu harga {verb} {sign}{zone_dist_pips:.0f} pips ke Key Zone {entry_zone} "
                f"(SL -{round(risk * 10):.0f}p aman di luar tembok)"
            )
            init_status = "PENDING_LIMIT"
        else:
            action_hint = str(raw_setup.get("status_message") or "News Guard Aktif — Tunggu volatilitas mereda")
            init_status = "ACTIVE"

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
            "setup_quality_score": setup_quality,
            "zone_proof": zone_proof,
            "zone_distance_pips": zone_dist_pips,
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
            "entry_reasons": entry_reasons[:4],
            "technical_rationale": str(rationale),
            "invalidation_level": str(invalidation),
            "status": init_status,
            "status_message": action_hint,
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
