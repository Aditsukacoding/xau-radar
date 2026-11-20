from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class NewsScenarioItem(BaseModel):
    label: str  # e.g., "Kuat (Hawkish Surprise)"
    condition: str  # e.g., "Actual >= 135K"
    yield_dxy_reaction: str  # e.g., "Yield US10Y & DXY melonjak tajam"
    gold_reaction: str  # e.g., "Emas tertekan keras; spekulan long terlikuidasi"
    target_area: str  # e.g., "Menguji 4.165, ekstensi ke 4.112"
    invalidation_level: str  # e.g., "Rejection kuat di atas 4.200"


class NewsIntelligenceResponse(BaseModel):
    symbol: str = "XAUUSD"
    currency: str = "USD"
    event_title: str
    scheduled_at_wib: str
    scheduled_at_utc: str
    actual: Optional[str] = None
    consensus: str
    previous: str
    market_regime: str
    market_regime_evidence: str
    fundamental_summary: str
    geopolitical_summary: str
    positioning_sentiment: str
    chart_condition_h4: str
    chart_condition_m30: str
    chart_condition_m5: str
    key_support_levels: List[float]
    key_resistance_levels: List[float]
    invalidation_level: str
    bias: str  # "BULLISH", "BEARISH", "NEUTRAL"
    confidence_level: str  # "Rendah", "Sedang", "Tinggi"
    scenarios: List[NewsScenarioItem]
    catalysts_to_watch: List[str]
    pending_catalysts: List[Dict[str, str]]
    intermarket_snapshot: Optional[Dict[str, Any]] = None  # Live DXY, US10Y, WTI & Market Regime
    event_comparison_note: str = ""  # Numeric Actual vs Forecast vs Previous comparison
    historical_reactions: List[Dict[str, Any]] = []  # Real 1H XAU pip reactions on recent USD releases
    historical_summary: str = ""  # Summary of historical news impact & volatility benchmark
    avg_historical_range_pips: float = 0.0
    disclaimer: str
    analyzed_at_wib: str
