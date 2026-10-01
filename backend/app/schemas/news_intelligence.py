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
    event_title: str
    scheduled_at_wib: str
    scheduled_at_utc: str
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
    disclaimer: str
    analyzed_at_wib: str
