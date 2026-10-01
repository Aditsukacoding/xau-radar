from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseDataProvider(ABC):
    @abstractmethod
    async def get_economic_calendar(self, days_ahead: int = 2) -> List[Dict[str, Any]]:
        """Fetch economic calendar events (scheduled, forecasts, previous)"""
        pass

    @abstractmethod
    async def get_news_articles(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch geopolitical and financial news with sentiment ratings"""
        pass

    @abstractmethod
    async def get_price_candles(self, symbol: str, timeframe: str, count: int = 100) -> List[Dict[str, Any]]:
        """Fetch OHLCV candlestick records"""
        pass

    @abstractmethod
    async def get_latest_price(self, symbol: str, force_refresh: bool = False, **kwargs) -> Dict[str, Any]:
        """Fetch real-time snapshot of the instrument price"""
        pass
