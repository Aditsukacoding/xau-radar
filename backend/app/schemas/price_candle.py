from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional


class PriceCandleBase(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str = "1h"
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class PriceCandleCreate(PriceCandleBase):
    pass


class PriceCandleResponse(PriceCandleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TechnicalIndicatorsResponse(BaseModel):
    symbol: str
    timeframe: str
    latest_price: float
    rsi_14: Optional[float] = None
    rsi_condition: Optional[str] = None  # OVERBOUGHT, OVERSOLD, NEUTRAL
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    trend_direction: str  # BULLISH, BEARISH, SIDEWAYS
    support_levels: List[float] = []
    resistance_levels: List[float] = []
    summary: str
