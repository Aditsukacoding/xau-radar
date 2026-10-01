from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
import random
import math
from app.providers.base import BaseDataProvider


class MockDataProvider(BaseDataProvider):
    """
    Realistic Mock Provider for XAU/USD and macro market data.
    Provides dynamically calculated dates relative to current UTC time.
    """

    async def get_latest_price(self, symbol: str = "XAUUSD", force_refresh: bool = False, **kwargs) -> Dict[str, Any]:
        # Realistic Gold base price with small micro fluctuation
        base_price = 2378.50
        noise = round((random.random() - 0.5) * 4.0, 2)
        current_price = round(base_price + noise, 2)
        open_price = 2364.20
        change = round(current_price - open_price, 2)
        change_pct = round((change / open_price) * 100, 2)

        return {
            "symbol": symbol,
            "name": "Gold vs US Dollar",
            "current_price": current_price,
            "open": open_price,
            "high": round(max(current_price, 2384.40), 2),
            "low": round(min(current_price, 2361.10), 2),
            "change_24h": change,
            "change_pct_24h": change_pct,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_price_candles(self, symbol: str = "XAUUSD", timeframe: str = "1h", count: int = 100) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        
        # Calculate time step per candle
        step_minutes = {
            "5m": 5,
            "15m": 15,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
        }.get(timeframe.lower(), 60)

        candles: List[Dict[str, Any]] = []
        base_price = 2340.0
        current_val = base_price

        for i in range(count):
            candle_time = now - timedelta(minutes=(count - i) * step_minutes)
            
            # Create smooth sinusoidal wave with realistic random walk
            trend = 0.05 * i
            cycle = 12.0 * math.sin(i / 8.0)
            noise = (random.random() - 0.48) * 3.5
            
            candle_open = round(current_val, 2)
            candle_close = round(base_price + trend + cycle + noise, 2)
            
            high_buffer = abs(random.gauss(1.5, 0.8))
            low_buffer = abs(random.gauss(1.5, 0.8))
            
            candle_high = round(max(candle_open, candle_close) + high_buffer, 2)
            candle_low = round(min(candle_open, candle_close) - low_buffer, 2)
            candle_vol = round(random.uniform(1200, 6500), 1)

            candles.append({
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": candle_time,
                "open": candle_open,
                "high": candle_high,
                "low": candle_low,
                "close": candle_close,
                "volume": candle_vol,
            })
            current_val = candle_close

        return candles

    async def get_economic_calendar(self, days_ahead: int = 2) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        
        # Realistic calendar events relative to current time
        events = [
            {
                "external_id": "mock_event_01",
                "currency": "USD",
                "event_title": "US Core CPI (MoM)",
                "impact_level": "HIGH",
                "scheduled_at": now + timedelta(hours=14),
                "actual_value": None,
                "forecast_value": "0.3%",
                "previous_value": "0.2%",
                "unit": "%",
                "sentiment_impact": "NEUTRAL",
            },
            {
                "external_id": "mock_event_02",
                "currency": "USD",
                "event_title": "Non-Farm Employment Change (NFP)",
                "impact_level": "HIGH",
                "scheduled_at": now + timedelta(hours=28),
                "actual_value": None,
                "forecast_value": "178K",
                "previous_value": "216K",
                "unit": "K",
                "sentiment_impact": "BEARISH_USD",
            },
            {
                "external_id": "mock_event_03",
                "currency": "USD",
                "event_title": "Unemployment Rate",
                "impact_level": "HIGH",
                "scheduled_at": now + timedelta(hours=28),
                "actual_value": None,
                "forecast_value": "4.1%",
                "previous_value": "4.0%",
                "unit": "%",
                "sentiment_impact": "BULLISH_GOLD",
            },
            {
                "external_id": "mock_event_04",
                "currency": "USD",
                "event_title": "FOMC Meeting Minutes",
                "impact_level": "HIGH",
                "scheduled_at": now - timedelta(hours=8),
                "actual_value": "Dovish Tone",
                "forecast_value": "Neutral",
                "previous_value": "Hawkish",
                "unit": "",
                "sentiment_impact": "BULLISH_GOLD",
            },
            {
                "external_id": "mock_event_05",
                "currency": "USD",
                "event_title": "Initial Jobless Claims",
                "impact_level": "MEDIUM",
                "scheduled_at": now - timedelta(hours=22),
                "actual_value": "228K",
                "forecast_value": "220K",
                "previous_value": "219K",
                "unit": "K",
                "sentiment_impact": "BEARISH_USD",
            },
        ]
        return events

    async def get_news_articles(self, symbol: str = "XAUUSD", limit: int = 10) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        
        articles = [
            {
                "symbol": symbol,
                "title": "Ketegangan Geopolitik Timur Tengah Memicu Permintaan Safe Haven Emas Meningkat",
                "source": "Reuters Global",
                "url": "https://www.reuters.com/markets/commodities/gold-safe-haven",
                "summary": "Ketidakpastian geopolitik di rute perdagangan internasional mendorong investor global meningkatkan alokasi lindung nilai pada emas batangan dan obligasi pemerintah.",
                "sentiment_label": "POSITIVE",
                "sentiment_score": 0.78,
                "published_at": now - timedelta(hours=2),
            },
            {
                "symbol": symbol,
                "title": "Ekspektasi Pemangkasan Suku Bunga The Fed Melemahkan Indeks Dolar (DXY)",
                "source": "Bloomberg Financial",
                "url": "https://www.bloomberg.com/news/articles/fed-rate-cut-expectations",
                "summary": "Pernyataan pejabat The Fed yang cenderung dovish membuka peluang pelonggaran moneter, memberi katalis positif bagi aset tanpa imbal hasil seperti XAU/USD.",
                "sentiment_label": "POSITIVE",
                "sentiment_score": 0.65,
                "published_at": now - timedelta(hours=5),
            },
            {
                "symbol": symbol,
                "title": "Bank Sentral Global Terus Borong Cadangan Emas Fisik pada Kuartal Ini",
                "source": "World Gold Council",
                "url": "https://www.gold.org/goldhub/research/gold-demand-trends",
                "summary": "Diversifikasi cadangan devisa oleh bank sentral negara berkembang terus menjadi pilar penopang harga emas di atas level psikologis $2350.",
                "sentiment_label": "POSITIVE",
                "sentiment_score": 0.72,
                "published_at": now - timedelta(hours=9),
            },
            {
                "symbol": symbol,
                "title": "Yield US Treasury 10-Tahun Naik Tipis, Membatasi Penguatan Logam Mulia Sementara",
                "source": "FXStreet",
                "url": "https://www.fxstreet.com/news/us-yields-tick-up",
                "summary": "Kenaikan yield obligasi pemerintah AS jangka 10 tahun memicu aksi ambil untung (profit taking) minor menjelang rilis data inflasi penting.",
                "sentiment_label": "NEGATIVE",
                "sentiment_score": -0.35,
                "published_at": now - timedelta(hours=15),
            },
            {
                "symbol": symbol,
                "title": "Volume Perdagangan Pasar Asia Terpantau Stabil Menjelang Rilis Data US Core CPI",
                "source": "ForexLive",
                "url": "https://www.forexlive.com/news/asian-session-gold-consolidation",
                "summary": "Para pelaku pasar bersikap wait-and-see menjaga rentang konsolidasi emas di kisaran support $2365 dan resistance $2390.",
                "sentiment_label": "NEUTRAL",
                "sentiment_score": 0.05,
                "published_at": now - timedelta(hours=20),
            },
        ]
        return articles[:limit]
