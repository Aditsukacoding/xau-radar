import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah Senior Institutional Macro & Quantitative Strategist untuk instrumen komoditas & forex (khususnya XAU/USD).
Kamu TIDAK menebak harga secara acak, melainkan menggunakan METODOLOGI INSTITUSIONAL 9 LANGKAH dengan integritas data mutlak:

ATURAN MUTLAK INTEGRITAS DATA & ZERO-HALLUCINATION:
1. HARGA AKTIF PASAR: Semua perhitungan level harga (Entry, Stop Loss, TP1, TP2, Support, Resistance) HARUS berpatokan presisi pada `current_price` yang diberikan dalam payload JSON input. JANGAN PERNAH mengarang harga historis (misal harga $1900-$2400 jika harga saat ini $4100+). Mengabaikan harga aktif adalah kesalahan fatal.
2. HUKUM FISIKA TRADING (TIDAK BOLEH DILANGGAR):
   - Jika Action = BUY: Stop Loss HARUS LEBIH RENDAH dari Entry (stop_loss < entry_price). TP1 & TP2 HARUS LEBIH TINGGI dari Entry (entry_price < take_profit_1 < take_profit_2).
   - Jika Action = SELL: Stop Loss HARUS LEBIH TINGGI dari Entry (stop_loss > entry_price). TP1 & TP2 HARUS LEBIH RENDAH dari Entry (take_profit_2 < take_profit_1 < entry_price).
   - Minimum Risk-to-Reward (R:R) 1 : 1.5. Entry zone harus realistis di sekitar harga aktif (pullback untuk BUY, rally untuk SELL).
3. PROFIL & GAYA TRADING USER (MUTLAK DISESUAIKAN):
   - STOP LOSS: Selalu targetkan di kisaran ~50 pips ($5.00 pada XAUUSD, toleransi 45-55 pips disesuaikan dengan swing low/high terdekat).
   - ZONA ENTRY: Lebar zona entry HARUS KETAT dan realistis, maksimal 15 - 20 pips ($1.50 - $2.00 dari titik acuan) di sekitar harga aktif.
     * Untuk BUY: Zona entry di sekitar harga aktif atau pullback kecil (misal $4171.00 - $4173.00). SL WAJIB berada di bawah seluruh zona entry.
     * Untuk SELL: Zona entry di sekitar harga aktif atau rally kecil (misal $4171.00 - $4173.00). SL WAJIB berada di atas seluruh zona entry.
     * JANGAN PERNAH membuat rentang zona entry puluhan dolar atau bertabrakan dengan Stop Loss / Take Profit!
   - TAKE PROFIT 1 (TP1): Kisaran 30 - 50 pips ($3.00 - $5.00) untuk mengunci profit pertama 50% dan memicu geser SL ke Breakeven (BEP).
   - TAKE PROFIT 2 (TP2 - RUNNER / NGEHOLD): Kisaran 80 - 100+ pips ($8.00 - $12.00+) untuk memaksimalkan swing hold.
   - Rasional Wajib: Jelaskan rencana eksekusi: amankan 50% posisi di TP1 (30-50 pips), geser SL ke Breakeven (BEP), dan tahan sisa posisi (ngehold) menuju target ekspansif TP2 (80-100+ pips).
4. BAHASA & STRUKTUR:
   - Gunakan Bahasa Indonesia yang santai tapi rapi, profesional, berbasis data nyata, tidak bertele-tele, dan terarah.
   - Tulis setiap field secara padat dan tajam (maksimal 2 kalimat per field ringkasan).

METODOLOGI 9 LANGKAH:
1. APA YANG DINANTI PASAR: Catat agenda kalender ekonomi, konsensus, dan rilis sebelumnya. Fokus pada DEVIASI angka aktual vs ekspektasi yang sudah priced-in.
2. REZIM PASAR (MARKET REGIME): Kenali rezim dominan (inflasi energi, pelonggaran suku bunga, flight-to-safety, atau likuiditas).
3. DATA FUNDAMENTAL: Kebijakan suku bunga Fed, inflasi (CPI/PCE), tenaga kerja (NFP/Claims), dan kurva Yield US10Y serta DXY.
4. TRANSMISI GEOPOLITIK: Dampak ke harga minyak mentah -> inflasi -> yield/dolar -> pengaruh ke daya tarik emas.
5. POSITIONING & SENTIMEN: Risiko crowded trade (posisi spekulan long vs short).
6. TEKNIKAL MULTI-TIMEFRAME: H4 (bias & zona besar), M30 (struktur pasar), M5 (konfirmasi reaksi).
7. SKENARIO TERUKUR: Proyeksikan skenario jika deviasi data kuat, sesuai konsensus, atau lemah.
8. SINTESIS & CONFIDENCE SCORE: Ukur keselarasan 4 pilar fundamental-geopolitik-positioning-teknikal (0-100%).
9. KATALIS TERTUNDA: Petakan agenda rilis mendatang sebagai pengingat bahwa analisis bersifat dinamis.

OUTPUT HARUS BERUPA JSON VALID TANPA MARKDOWN WRAPPER:
{
  "bias": "BULLISH" | "BEARISH" | "NEUTRAL",
  "confidence_score": integer (50-95),
  "summary": "Ringkasan kesimpulan bias 2 kalimat yang mengintegrasikan rezim pasar dan ekspektasi konsensus",
  "fundamental_notes": "Analisis kebijakan Fed, deviasi inflasi/tenaga kerja, serta arah Yield US10Y & DXY",
  "geopolitical_notes": "Analisis geopolitik melalui jalur transmisi dampak harga minyak dan sentimen safe-haven",
  "technical_notes": "Analisis multi-timeframe H4-M30-M5, posisi supply/demand, dan reaksi di chart TradingView",
  "key_levels": {
    "support": [number, number],
    "resistance": [number, number]
  },
  "trade_setup": {
    "action": "BUY" | "SELL" | "WAIT",
    "action_label": "BUY (LONG) ON PULLBACK" | "SELL (SHORT) ON RALLY" | "WAIT / STANDBY",
    "entry_zone": "$4200.00 - $4204.00",
    "entry_price": 4202.00,
    "stop_loss": 4197.00,
    "take_profit_1": 4206.00,
    "take_profit_2": 4211.50,
    "risk_reward_ratio": "1 : 1.9",
    "risk_pips": 50.0,
    "reward_tp1_pips": 40.0,
    "reward_tp2_pips": 95.0,
    "technical_rationale": "Setup disesuaikan profil trader: Pasang SL 50 pips ($4197.00). Kunci profit 50% lot di TP1 +40 pips ($4206.00) dan geser SL ke BEP (Breakeven). Tahan (hold) sisa posisi menuju swing TP2 +95 pips ($4211.50).",
    "invalidation_level": "Level harga persis yang membatalkan skenario ini bila ditembus"
  },
  "risk_factors": [
    "Faktor risiko 1 yang dapat membatalkan bias",
    "Faktor risiko 2"
  ],
  "sources": [
    "Kalender Ekonomi ForexFactory",
    "Chart Teknikal TradingView & Indikator H1",
    "Arus Berita Geopolitik & Makro Global"
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
    ) -> Dict[str, Any]:
        """
        Synthesizes 3-pillar market data using Claude API, Gemini API, or intelligent heuristic fallback,
        followed by a mandatory programmatic validation and sanitization layer.
        """
        curr_price = float(price_snapshot.get("current_price", 4198.50))
        payload_data = {
            "symbol": symbol,
            "current_price": curr_price,
            "technical": technical_data,
            "upcoming_economic_events": economic_events[:4],
            "recent_news_sentiment": news_articles[:4],
        }

        # 1. Try Anthropic Claude API if key exists
        if settings.ANTHROPIC_API_KEY:
            try:
                raw_claude = await AIAgentEngine._call_claude_api(payload_data)
                sanitized = AIAgentEngine._sanitize_and_validate_trade_setup(
                    raw_claude,
                    curr_price=curr_price,
                    technical_data=technical_data,
                    economic_events=economic_events,
                    news_articles=news_articles
                )
                logger.info("[AIAgentEngine] Claude analysis successfully synthesized and sanitized!")
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
                    technical_data=technical_data,
                    economic_events=economic_events,
                    news_articles=news_articles
                )
                logger.info("[AIAgentEngine] Gemini analysis successfully synthesized and sanitized!")
                return sanitized
            except Exception as e:
                logger.warning(f"Gemini API failed, trying OpenRouter fallback: {e}")

        # 3. Try OpenRouter API (FREE — 200+ models, same key as portfolio chatbot)
        if settings.OPENROUTER_API_KEY:
            try:
                raw_openrouter = await AIAgentEngine._call_openrouter_api(payload_data)
                sanitized = AIAgentEngine._sanitize_and_validate_trade_setup(
                    raw_openrouter,
                    curr_price=curr_price,
                    technical_data=technical_data,
                    economic_events=economic_events,
                    news_articles=news_articles
                )
                logger.info("[AIAgentEngine] OpenRouter analysis successfully synthesized and sanitized!")
                return sanitized
            except Exception as e:
                logger.warning(f"OpenRouter API failed, falling back to heuristic: {e}")

        # 4. Built-in Quantitative Heuristic Synthesizer (Zero-cost, works offline)
        raw_heuristic = AIAgentEngine._heuristic_synthesis(symbol, price_snapshot, technical_data, economic_events, news_articles)
        return AIAgentEngine._sanitize_and_validate_trade_setup(
            raw_heuristic,
            curr_price=curr_price,
            technical_data=technical_data,
            economic_events=economic_events,
            news_articles=news_articles
        )

    @staticmethod
    async def _call_claude_api(data: Dict[str, Any]) -> Dict[str, Any]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        models = [
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-5-20250929",
            "claude-sonnet-5",
            "claude-sonnet-4-6",
        ]
        last_error = None
        for model in models:
            body = {
                "model": model,
                "max_tokens": 4096,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analisis data pasar berikut dan berikan kesimpulan bias dalam format JSON:\n{json.dumps(data, default=str)}"
                    }
                ]
            }
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(url, json=body, headers=headers)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        content_text = res_json["content"][0]["text"].strip()
                        s_idx = content_text.find("{")
                        e_idx = content_text.rfind("}")
                        if s_idx != -1 and e_idx != -1 and e_idx > s_idx:
                            clean_json = content_text[s_idx:e_idx + 1]
                        else:
                            clean_json = content_text
                        parsed = json.loads(clean_json)
                        logger.info(f"[AIAgentEngine] Anthropic {model} analysis successfully synthesized!")
                        return parsed
                    else:
                        last_error = resp.text
                        logger.warning(f"Claude {model} returned status {resp.status_code}: {resp.text}")
            except Exception as e:
                last_error = e
                logger.warning(f"Claude {model} call error: {e}")

        raise RuntimeError(f"All Claude models failed. Last error: {last_error}")

    @staticmethod
    async def _call_gemini_api(data: Dict[str, Any]) -> Dict[str, Any]:
        # Try gemini-1.5-flash first, then gemini-2.0-flash as fallback
        models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        last_error = None

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
            body = {
                "contents": [
                    {
                        "parts": [
                            {"text": SYSTEM_PROMPT},
                            {"text": f"Analisis data pasar berikut dan hasilkan JSON:\n{json.dumps(data, default=str)}"}
                        ]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.2
                }
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=body)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        candidates = res_json.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and "text" in parts[0]:
                                content_text = parts[0]["text"].strip()
                                if content_text.startswith("```json"):
                                    content_text = content_text[7:]
                                elif content_text.startswith("```"):
                                    content_text = content_text[3:]
                                if content_text.endswith("```"):
                                    content_text = content_text[:-3]
                                parsed = json.loads(content_text.strip())
                                logger.info(f"[AIAgentEngine] Google {model} analysis successfully synthesized!")
                                return parsed
                    else:
                        last_error = f"{model} returned HTTP {resp.status_code}: {resp.text[:150]}"
            except Exception as e:
                last_error = str(e)
                continue

        raise RuntimeError(f"All Gemini models failed: {last_error}")

    @staticmethod
    async def _call_openrouter_api(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls OpenRouter.ai — a free-tier gateway to 200+ LLMs (Qwen, Gemma, Mistral, etc.).
        Uses the same OPENROUTER_API_KEY as the portfolio chatbot (sk-or-v1-...).
        Tries multiple free models in sequence as an internal fallback chain.
        """
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://xauusd-radar.app",
            "X-Title": "XAU/USD RADAR — Institutional Bias Engine",
        }
        # Free model priority order: strongest first, lightest last as safety net
        # List verified on 2026-10-01 from openrouter.ai/api/v1/models
        free_models = [
            "nvidia/nemotron-3-ultra-550b-a55b:free",  # 550B param — strongest available
            "qwen/qwen3.8-27b:free",                   # Qwen 3.8 27B — solid reasoning
            "google/gemma-4-31b-it:free",              # Google Gemma 4 31B
            "google/gemma-4-26b-a4b-it:free",          # Google Gemma 4 26B MoE
            "nvidia/nemotron-3-super-120b-a12b:free",  # Nvidia Nemotron 120B
            "nvidia/nemotron-3.5-lightning:free",       # Nvidia fast model
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
                                f"Analisis data pasar berikut dan berikan kesimpulan bias "
                                f"dalam format JSON yang valid:\n{json.dumps(data, default=str)}"
                            ),
                        },
                    ],
                    "max_tokens": 2048,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                }
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(url, json=body, headers=headers)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        content_text = res_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        if not content_text:
                            logger.warning(f"[OpenRouter] {model} returned empty content.")
                            continue
                        # Extract JSON block robustly
                        if content_text.startswith("```json"):
                            content_text = content_text[7:]
                        elif content_text.startswith("```"):
                            content_text = content_text[3:]
                        if content_text.endswith("```"):
                            content_text = content_text[:-3]
                        s_idx = content_text.find("{")
                        e_idx = content_text.rfind("}")
                        if s_idx != -1 and e_idx != -1 and e_idx > s_idx:
                            content_text = content_text[s_idx:e_idx + 1]
                        parsed = json.loads(content_text.strip())
                        logger.info(f"[AIAgentEngine] OpenRouter/{model} analysis synthesized!")
                        return parsed
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                        logger.warning(f"[OpenRouter] {model} returned {resp.status_code}")
            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {e}"
                logger.warning(f"[OpenRouter] {model} JSON parse failed: {e}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[OpenRouter] {model} call error: {e}")

        raise RuntimeError(f"All OpenRouter models failed. Last error: {last_error}")

    @staticmethod
    def _heuristic_synthesis(
        symbol: str,
        price_snapshot: Dict[str, Any],
        technical_data: Dict[str, Any],
        economic_events: List[Dict[str, Any]],
        news_articles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Deterministic, rule-based quantitative synthesizer that mimics LLM output format.
        Combines Fundamental (35%), Geopolitical (30%), and Technical (35%) scores.
        """
        curr_price = price_snapshot.get("current_price", 2378.0)

        # 1. Technical Score (-1.0 to 1.0)
        tech_dir = technical_data.get("trend_direction", "SIDEWAYS")
        tech_score = 0.8 if tech_dir == "BULLISH" else (-0.8 if tech_dir == "BEARISH" else 0.0)

        # 2. Geopolitical Sentiment Score (-1.0 to 1.0)
        news_scores = [n.get("sentiment_score", 0.0) for n in news_articles]
        geo_score = sum(news_scores) / len(news_scores) if news_scores else 0.0

        # 3. Fundamental Score (-1.0 to 1.0)
        # Gold tends to be Bullish when US data is weak or Fed is dovish
        fund_score = 0.5  # default moderately bullish bias due to rate cut expectations
        for event in economic_events:
            impact = event.get("sentiment_impact", "")
            if "BULLISH_GOLD" in impact or "BEARISH_USD" in impact:
                fund_score += 0.2
            elif "BEARISH_GOLD" in impact or "BULLISH_USD" in impact:
                fund_score -= 0.2
        fund_score = max(-1.0, min(1.0, fund_score))

        # Weighted Total Score: -1.0 (Strong Bearish) to +1.0 (Strong Bullish)
        composite_score = (fund_score * 0.35) + (geo_score * 0.30) + (tech_score * 0.35)

        if composite_score > 0.25:
            bias = "BULLISH"
            confidence = int(60 + (composite_score * 35))
            summary = (
                f"Pasar {symbol} menunjukkan bias Bullish kuat yang didorong oleh sinyal teknikal ekspansif "
                f"serta sentimen safe-haven geopolitik global yang solid."
            )
        elif composite_score < -0.25:
            bias = "BEARISH"
            confidence = int(60 + (abs(composite_score) * 35))
            summary = (
                f"Pasar {symbol} condong ke bias Bearish akibat tekanan penguatan Dolar dan "
                f"penolakan harga di zona resistance teknikal utama."
            )
        else:
            bias = "NEUTRAL"
            confidence = int(50 + (abs(composite_score) * 20))
            summary = (
                f"Pasar {symbol} berada dalam fase konsolidasi (Netral). Pelaku pasar bersikap wait-and-see "
                f"menjelang rilis agenda kalender ekonomi high-impact terdekat."
            )

        confidence = max(50, min(95, confidence))

        supports = technical_data.get("support_levels", [round(curr_price * 0.99, 2)])
        resistances = technical_data.get("resistance_levels", [round(curr_price * 1.01, 2)])

        sources = []
        if economic_events:
            sources.append(f"Kalender Ekonomi: {economic_events[0].get('event_title', 'Data Rilis')}")
        if news_articles:
            sources.append(f"Berita Global: {news_articles[0].get('title', 'Headline Terkini')[:50]}...")
        sources.append("Struktur Grafik Harga & Indikator Moving Average/RSI")

        risks = [
            "Volatilitas ekstrem pasca rilis berita high impact (NFP / CPI) berpotensi membalikkan struktur harga",
            f"Penembusan batas teknikal di bawah Support ${supports[0] if supports else 'kunci'}"
        ]

        # Calculate exact entry, SL, TP1, and TP2 from chart & high-impact news
        trade_setup = AIAgentEngine._generate_trade_setup(
            symbol=symbol,
            curr_price=curr_price,
            bias=bias,
            supports=supports,
            resistances=resistances,
            technical_data=technical_data,
            economic_events=economic_events,
            news_articles=news_articles,
        )

        return {
            "bias": bias,
            "confidence_score": confidence,
            "summary": summary,
            "fundamental_notes": (
                "Ekspektasi kebijakan suku bunga AS dan agenda kalender ekonomi mendatang "
                "menjadi penggerak utama sentimen pasar jangka menengah."
            ),
            "geopolitical_notes": (
                "Kekhawatiran rantai pasok global dan tensi geopolitik mempertahankan minat likuiditas pada safe haven."
            ),
            "technical_notes": technical_data.get("summary", "Indikator teknikal mengindikasikan momentum seimbang."),
            "key_levels": {
                "support": supports,
                "resistance": resistances,
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
        economic_events: List[Dict[str, Any]],
        news_articles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Synthesizes technical chart structure (Support/Resistance, SMA 20/50, RSI)
        and high-impact event sentiment to formulate execution levels:
        Entry Zone, TP1, TP2, and Stop Loss (SL).
        """
        valid_supports = sorted([s for s in supports if s < curr_price])
        valid_resistances = sorted([r for r in resistances if r > curr_price])

        primary_sup = valid_supports[-1] if valid_supports else round(curr_price - 10.0, 2)
        secondary_sup = valid_supports[-2] if len(valid_supports) >= 2 else round(primary_sup - 12.0, 2)

        primary_res = valid_resistances[0] if valid_resistances else round(curr_price + 10.0, 2)
        secondary_res = valid_resistances[1] if len(valid_resistances) >= 2 else round(primary_res + 14.0, 2)

        # High impact catalyst summary
        high_impact_news = [e for e in economic_events if e.get("impact_level") == "HIGH"]
        catalyst_desc = (
            f"katalis rilis '{high_impact_news[0].get('event_title')}'"
            if high_impact_news
            else "sentimen arus makro & geopolitik terkini"
        )

        if bias == "BULLISH":
            action = "BUY"
            action_label = "BUY (LONG) ON PULLBACK"
            entry_price = round(curr_price, 2)
            entry_low = round(entry_price - 1.0, 2)
            entry_high = round(entry_price + 1.0, 2)
            entry_zone = f"${entry_low:.2f} - ${entry_high:.2f}"

            # Stop loss targeted to user preference: ~50 pips ($5.00), strictly below entry zone
            stop_loss = round(entry_price - 5.0, 2)
            risk = round(entry_price - stop_loss, 2)

            # TP1 targeted to user preference: 30-50 pips (~$4.00)
            tp1 = round(entry_price + 4.0, 2)

            # TP2 targeted to user preference: 80-100+ pips (~$9.50) for hold runner
            tp2 = round(entry_price + 9.5, 2)

            reward1 = round(tp1 - entry_price, 2)
            reward2 = round(tp2 - entry_price, 2)
            rrr = f"1 : {round(reward2 / risk, 1)}" if risk > 0 else "1 : 1.9"

            rationale = (
                f"Sintesis 3 pilar mengonfirmasi setup Bullish didukung {catalyst_desc}. "
                f"Rencana eksekusi: Ambil posisi Buy di zona ketat {entry_zone} dengan proteksi Stop Loss "
                f"terukur 50 pips di ${stop_loss:.2f} (di bawah batas zona). "
                f"Kunci profit 50% lot saat harga mencapai TP1 ${tp1:.2f} (+40 pips) dan segera geser SL ke Breakeven (BEP). "
                f"Tahan (hold) sisa posisi untuk mengejar target swing ekspansi TP2 di ${tp2:.2f} (+95 pips)."
            )
            invalidation = f"Candle H1 ditutup di bawah level support ${stop_loss:.2f} membatalkan validitas setup bullish ini."

        elif bias == "BEARISH":
            action = "SELL"
            action_label = "SELL (SHORT) ON RALLY"
            entry_price = round(curr_price, 2)
            entry_low = round(entry_price - 1.0, 2)
            entry_high = round(entry_price + 1.0, 2)
            entry_zone = f"${entry_low:.2f} - ${entry_high:.2f}"

            # Stop loss targeted to user preference: ~50 pips ($5.00), strictly above entry zone
            stop_loss = round(entry_price + 5.0, 2)
            risk = round(stop_loss - entry_price, 2)

            # TP1 targeted to user preference: 30-50 pips (~$4.00)
            tp1 = round(entry_price - 4.0, 2)

            # TP2 targeted to user preference: 80-100+ pips (~$9.50) for hold runner
            tp2 = round(entry_price - 9.5, 2)

            reward1 = round(entry_price - tp1, 2)
            reward2 = round(entry_price - tp2, 2)
            rrr = f"1 : {round(reward2 / risk, 1)}" if risk > 0 else "1 : 1.9"

            rationale = (
                f"Tekanan jual makro dan teknikal mengonfirmasi setup Bearish didukung {catalyst_desc}. "
                f"Rencana eksekusi: Ambil posisi Sell di zona ketat {entry_zone} dengan proteksi Stop Loss "
                f"terukur 50 pips di ${stop_loss:.2f} (di atas batas zona). "
                f"Kunci profit parsial di TP1 ${tp1:.2f} (+40 pips) dan amankan posisi dengan geser SL ke Breakeven (BEP). "
                f"Tahan (hold) sisa lot untuk mengejar target swing pelemahan lanjutan TP2 di ${tp2:.2f} (+95 pips)."
            )
            invalidation = f"Candle H1 ditutup di atas ${stop_loss:.2f} membatalkan validitas skenario bearish."

        else:
            action = "WAIT"
            action_label = "WAIT / STANDBY (BREAKOUT STRADDLE)"
            entry_price = curr_price
            entry_zone = f"Breakout > ${primary_res:.2f} ATAU Breakdown < ${primary_sup:.2f}"
            stop_loss = round(primary_sup - 5.0, 2)
            tp1 = round(primary_res + 8.0, 2)
            tp2 = round(primary_res + 18.0, 2)
            risk = 8.0
            reward1 = 10.0
            reward2 = 20.0
            rrr = "1 : 2.0"
            rationale = (
                f"Pasar berada di fase konsolidasi menyempit di antara Support ${primary_sup:.2f} dan "
                f"Resistance ${primary_res:.2f} menantikan rilis {catalyst_desc}. Disarankan menahan diri "
                f"(Wait & See) hingga terbentuk candle konfirmasi penembusan arah (Breakout) sebelum membuka posisi baru."
            )
            invalidation = "Volatilitas liar pasca rilis berita tanpa tren berkelanjutan (whipsaw)."

        return {
            "action": action,
            "action_label": action_label,
            "entry_zone": entry_zone,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit_1": tp1,
            "take_profit_2": tp2,
            "risk_reward_ratio": rrr,
            "risk_pips": round(risk * 10, 1),
            "reward_tp1_pips": round(reward1 * 10, 1),
            "reward_tp2_pips": round(reward2 * 10, 1),
            "technical_rationale": rationale,
            "invalidation_level": invalidation,
            "status": "ACTIVE",
            "status_message": f"Setup {action} Terkunci (Titik Acuan: ${entry_price:.2f}). Menunggu konfirmasi target/SL.",
        }

    @staticmethod
    def _sanitize_and_validate_trade_setup(
        raw_data: Any,
        curr_price: float,
        technical_data: Optional[Dict[str, Any]] = None,
        economic_events: Optional[List[Dict[str, Any]]] = None,
        news_articles: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Anti-Hallucination Guardrail & Sanitizer:
        Ensures 100% adherence to live market prices, trading physics, and mathematical laws:
        1. Guarantees prices anchor to curr_price (no pre-2024 cutoff hallucinations).
        2. BUY physics: Stop Loss < Entry Price < Take Profit 1 < Take Profit 2.
        3. SELL physics: Stop Loss > Entry Price > Take Profit 1 > Take Profit 2.
        4. Re-calculates pip distances and Risk-to-Reward ratio with exact precision.
        5. Sanitizes support/resistance levels.
        """
        if not isinstance(raw_data, dict):
            raw_data = {}

        # 1. Bias normalization
        bias = str(raw_data.get("bias", "NEUTRAL")).strip().upper()
        if bias not in ["BULLISH", "BEARISH", "NEUTRAL"]:
            bias = "NEUTRAL"

        # 2. Confidence Score
        try:
            confidence = int(raw_data.get("confidence_score", 70))
        except (ValueError, TypeError):
            confidence = 70
        confidence = max(50, min(95, confidence))

        # 3. Key Levels (Support & Resistance)
        key_levels = raw_data.get("key_levels", {})
        if not isinstance(key_levels, dict):
            key_levels = {}
        raw_sups = key_levels.get("support", [])
        raw_res = key_levels.get("resistance", [])

        # Filter and validate supports (must be < curr_price and within 15% band)
        valid_sups: List[float] = []
        if isinstance(raw_sups, list):
            for s in raw_sups:
                try:
                    sf = round(float(s), 2)
                    if (curr_price * 0.85) < sf < curr_price:
                        valid_sups.append(sf)
                except (ValueError, TypeError):
                    continue
        valid_sups = sorted(list(set(valid_sups)), reverse=True)
        if not valid_sups:
            tech_sups = (technical_data or {}).get("support_levels", [])
            valid_sups = [round(float(s), 2) for s in tech_sups if (curr_price * 0.85) < float(s) < curr_price]
            if not valid_sups:
                valid_sups = [round(curr_price - 18.0, 2), round(curr_price - 38.0, 2)]

        # Filter and validate resistances (must be > curr_price and within 15% band)
        valid_res: List[float] = []
        if isinstance(raw_res, list):
            for r in raw_res:
                try:
                    rf = round(float(r), 2)
                    if curr_price < rf < (curr_price * 1.15):
                        valid_res.append(rf)
                except (ValueError, TypeError):
                    continue
        valid_res = sorted(list(set(valid_res)))
        if not valid_res:
            tech_res = (technical_data or {}).get("resistance_levels", [])
            valid_res = [round(float(r), 2) for r in tech_res if curr_price < float(r) < (curr_price * 1.15)]
            if not valid_res:
                valid_res = [round(curr_price + 18.0, 2), round(curr_price + 38.0, 2)]

        primary_sup = valid_sups[0]
        secondary_sup = valid_sups[1] if len(valid_sups) > 1 else round(primary_sup - 15.0, 2)
        primary_res = valid_res[0]
        secondary_res = valid_res[1] if len(valid_res) > 1 else round(primary_res + 15.0, 2)

        # 4. Trade Setup Validation & Trading Law Enforcement
        raw_setup = raw_data.get("trade_setup", {})
        if not isinstance(raw_setup, dict):
            raw_setup = {}

        action = str(raw_setup.get("action", "")).strip().upper()
        if action not in ["BUY", "SELL", "WAIT"]:
            action = "BUY" if bias == "BULLISH" else ("SELL" if bias == "BEARISH" else "WAIT")

        # Entry Price Validation: Snaps to near live price if AI hallucinated or strayed too far
        try:
            entry_p = float(raw_setup.get("entry_price", curr_price))
            # If entry_p is more than $3.50 away from live curr_price, snap to near price
            if abs(entry_p - curr_price) > 3.50:
                logger.warning(f"[Guardrail] AI entry_price ${entry_p} far from live ${curr_price}, snapping near market")
                if action == "BUY":
                    entry_p = round(curr_price - 0.50, 2)
                elif action == "SELL":
                    entry_p = round(curr_price + 0.50, 2)
                else:
                    entry_p = round(curr_price, 2)
        except (ValueError, TypeError):
            entry_p = curr_price

        # Enforce Trading Physics & User Strategy (SL ~50 pips, TP1 30-50 pips, TP2 80-100+ pips hold):
        if action == "BUY":
            action_label = "BUY (LONG) ON PULLBACK"
            entry_price = round(entry_p, 2)
            # Tight realistic execution zone: 15-20 pips ($1.50 - $2.00 pocket)
            entry_low = round(entry_price - 1.00, 2)
            entry_high = round(entry_price + 1.00, 2)
            entry_zone = f"${entry_low:.2f} - ${entry_high:.2f}"

            # Stop Loss MUST BE STRICTLY LESS THAN entry_low, calibrated to ~50 pips ($5.00)
            try:
                sl = float(raw_setup.get("stop_loss", 0))
            except (ValueError, TypeError):
                sl = 0
            if sl >= entry_low or abs(entry_price - sl) > 5.5 or abs(entry_price - sl) < 4.5:
                sl = round(entry_price - 5.0, 2)

            risk = round(entry_price - sl, 2)
            if risk <= 0:
                risk = 5.0
                sl = round(entry_price - 5.0, 2)

            # Take Profit 1 MUST BE GREATER THAN entry_high, calibrated to 30-50 pips ($3.00 - $5.00)
            try:
                tp1 = float(raw_setup.get("take_profit_1", 0))
            except (ValueError, TypeError):
                tp1 = 0
            if tp1 <= entry_high or abs(tp1 - entry_price) > 5.0 or abs(tp1 - entry_price) < 3.0:
                tp1 = round(entry_price + 4.0, 2)

            # Take Profit 2 MUST BE GREATER THAN tp1, calibrated to 80-150 pips ($8.00 - $15.00) for hold runner
            try:
                tp2 = float(raw_setup.get("take_profit_2", 0))
            except (ValueError, TypeError):
                tp2 = 0
            if tp2 <= tp1 or abs(tp2 - entry_price) < 8.0 or abs(tp2 - entry_price) > 16.0:
                tp2 = round(entry_price + 9.5, 2)

            reward1 = round(tp1 - entry_price, 2)
            reward2 = round(tp2 - entry_price, 2)
            rrr = f"1 : {round(reward2 / risk, 1)}" if risk > 0 else "1 : 1.9"

            rationale = (
                f"Setup disesuaikan profil trader: Pasang Stop Loss ~50 pips di ${sl:.2f} (di bawah batas zona). "
                f"Kunci profit parsial 50% di TP1 ${tp1:.2f} (+{round(reward1 * 10):.0f} pips) dan segera geser SL ke Breakeven (BEP). "
                f"Tahan (hold) sisa posisi untuk mengejar target swing ekspansi TP2 di ${tp2:.2f} (+{round(reward2 * 10):.0f} pips)."
            )
            invalidation = f"Candle H1 ditutup di bawah level support ${sl:.2f} membatalkan validitas skenario bullish."

        elif action == "SELL":
            action_label = "SELL (SHORT) ON RALLY"
            entry_price = round(entry_p, 2)
            # Tight realistic execution zone: 15-20 pips ($1.50 - $2.00 pocket)
            entry_low = round(entry_price - 1.00, 2)
            entry_high = round(entry_price + 1.00, 2)
            entry_zone = f"${entry_low:.2f} - ${entry_high:.2f}"

            # Stop Loss MUST BE STRICTLY GREATER THAN entry_high, calibrated to ~50 pips ($5.00)
            try:
                sl = float(raw_setup.get("stop_loss", 0))
            except (ValueError, TypeError):
                sl = 0
            if sl <= entry_high or abs(sl - entry_price) > 5.5 or abs(sl - entry_price) < 4.5:
                sl = round(entry_price + 5.0, 2)

            risk = round(sl - entry_price, 2)
            if risk <= 0:
                risk = 5.0
                sl = round(entry_price + 5.0, 2)

            # Take Profit 1 MUST BE LESS THAN entry_low, calibrated to 30-50 pips ($3.00 - $5.00)
            try:
                tp1 = float(raw_setup.get("take_profit_1", 0))
            except (ValueError, TypeError):
                tp1 = 0
            if tp1 >= entry_low or abs(entry_price - tp1) > 5.0 or abs(entry_price - tp1) < 3.0:
                tp1 = round(entry_price - 4.0, 2)

            # Take Profit 2 MUST BE LESS THAN tp1, calibrated to 80-150 pips ($8.00 - $15.00) for hold runner
            try:
                tp2 = float(raw_setup.get("take_profit_2", 0))
            except (ValueError, TypeError):
                tp2 = 0
            if tp2 >= tp1 or abs(entry_price - tp2) < 8.0 or abs(entry_price - tp2) > 16.0:
                tp2 = round(entry_price - 9.5, 2)

            reward1 = round(entry_price - tp1, 2)
            reward2 = round(entry_price - tp2, 2)
            rrr = f"1 : {round(reward2 / risk, 1)}" if risk > 0 else "1 : 1.9"

            rationale = (
                f"Setup disesuaikan profil trader: Pasang Stop Loss ~50 pips di ${sl:.2f} (di atas batas zona). "
                f"Kunci profit parsial 50% di TP1 ${tp1:.2f} (+{round(reward1 * 10):.0f} pips) dan amankan posisi dengan geser SL ke Breakeven (BEP). "
                f"Tahan (hold) sisa lot untuk mengejar target swing pelemahan lanjutan TP2 di ${tp2:.2f} (+{round(reward2 * 10):.0f} pips)."
            )
            invalidation = f"Candle H1 ditutup di atas ${sl:.2f} membatalkan validitas skenario bearish."

        else:
            action = "WAIT"
            action_label = "WAIT / STANDBY (BREAKOUT STRADDLE)"
            entry_price = round(curr_price, 2)
            entry_zone = f"Breakout > ${primary_res:.2f} ATAU Breakdown < ${primary_sup:.2f}"
            sl = round(primary_sup - 5.0, 2)
            tp1 = round(primary_res + 8.0, 2)
            tp2 = round(primary_res + 18.0, 2)
            risk = 8.0
            reward1 = 10.0
            reward2 = 20.0
            rrr = "1 : 2.0"
            rationale = raw_setup.get("technical_rationale")
            if not rationale or len(str(rationale).strip()) < 20:
                rationale = (
                    f"Harga berkonsolidasi di rentang Support ${primary_sup:.2f} dan Resistance ${primary_res:.2f}. "
                    f"Disarankan menahan diri (Standby) dan menunggu konfirmasi penembusan arah (Breakout) yang jelas."
                )
            invalidation = "Volatilitas liar pasca rilis berita tanpa tren berkelanjutan (whipsaw)."

        trade_setup = {
            "action": action,
            "action_label": action_label,
            "entry_zone": entry_zone,
            "entry_price": entry_price,
            "stop_loss": sl,
            "take_profit_1": tp1,
            "take_profit_2": tp2,
            "risk_reward_ratio": rrr,
            "risk_pips": round(risk * 10, 1),
            "reward_tp1_pips": round(reward1 * 10, 1),
            "reward_tp2_pips": round(reward2 * 10, 1),
            "technical_rationale": str(rationale),
            "invalidation_level": str(invalidation),
            "status": "ACTIVE",
            "status_message": f"Setup {action} Terkunci (Titik Acuan: ${entry_price:.2f}). Menunggu konfirmasi target/SL.",
        }

        # 5. Clean Summaries and Notes
        summary = str(raw_data.get("summary", "")).strip()
        if not summary:
            summary = f"Analisis XAUUSD mengonfirmasi bias {bias} dengan tingkat keyakinan {confidence}%, berpatokan pada level teknikal ${curr_price:.2f}."

        fund_notes = str(raw_data.get("fundamental_notes", "")).strip()
        if not fund_notes:
            fund_notes = "Sentimen suku bunga The Fed dan dinamika inflasi/tenaga kerja AS menjadi jangkar utama pergerakan harga."

        geo_notes = str(raw_data.get("geopolitical_notes", "")).strip()
        if not geo_notes:
            geo_notes = "Transmisi tensi geopolitik global dan harga komoditas energi menopang permintaan safe-haven emas."

        tech_notes = str(raw_data.get("technical_notes", "")).strip()
        if not tech_notes:
            tech_notes = f"Struktur chart menguji level Support ${primary_sup:.2f} dan Resistance ${primary_res:.2f}."

        # 6. Risk factors & Sources
        raw_risks = raw_data.get("risk_factors", [])
        if not isinstance(raw_risks, list) or not raw_risks:
            risks = [
                "Volatilitas tajam pasca rilis kalender ekonomi high-impact berpotensi menguji batas invalidasi.",
                f"Penembusan harga di luar rentang ${primary_sup:.2f} - ${primary_res:.2f} membatalkan validitas skenario."
            ]
        else:
            risks = [str(r) for r in raw_risks if str(r).strip()][:4]

        raw_sources = raw_data.get("sources", [])
        if not isinstance(raw_sources, list) or not raw_sources:
            sources = [
                "Kalender Ekonomi Resmi ForexFactory",
                "Chart Teknikal TradingView & Indikator Moving Average/RSI",
                "Arus Berita Makroekonomi & Geopolitik Global"
            ]
        else:
            sources = [str(s) for s in raw_sources if str(s).strip()][:4]

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
