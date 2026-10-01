from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Dict, Any, Optional


class KeyLevels(BaseModel):
    support: List[float] = []
    resistance: List[float] = []


class TradeSetup(BaseModel):
    action: str = "WAIT"  # BUY, SELL, WAIT
    action_label: str = "WAIT / STANDBY"  # e.g. BUY (LONG), SELL (SHORT), WAIT / MONITOR
    entry_zone: str = ""  # e.g. $4202.00 - $4208.50
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    risk_reward_ratio: str = "1 : 2.0"
    risk_pips: float = 0.0
    reward_tp1_pips: float = 0.0
    reward_tp2_pips: float = 0.0
    technical_rationale: str = ""
    invalidation_level: str = ""
    status: str = "ACTIVE"  # ACTIVE, RUNNING_TP1_HIT, COMPLETED, STOPPED_OUT
    status_message: str = "Setup Konsisten Terkunci (Menunggu Target / SL)"


class AnalysisReportBase(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str = "1h"
    bias: str  # BULLISH, BEARISH, NEUTRAL
    confidence_score: int  # 0 to 100
    summary: str
    fundamental_notes: Optional[str] = None
    geopolitical_notes: Optional[str] = None
    technical_notes: Optional[str] = None
    key_levels: KeyLevels = KeyLevels()
    trade_setup: Optional[TradeSetup] = None
    risk_factors: List[str] = []
    sources: List[str] = []
    disclaimer: str


class AnalysisReportCreate(AnalysisReportBase):
    pass


class AnalysisReportResponse(BaseModel):
    id: int
    symbol: str
    timeframe: str
    bias: str
    confidence_score: int
    summary: str
    fundamental_notes: Optional[str] = None
    geopolitical_notes: Optional[str] = None
    technical_notes: Optional[str] = None
    key_levels: KeyLevels
    trade_setup: Optional[TradeSetup] = None
    risk_factors: List[str] = []
    sources: List[str] = []
    disclaimer: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardSummaryResponse(BaseModel):
    symbol: str
    instrument_name: str
    current_price: float
    price_change_24h: float
    price_change_pct_24h: float
    high_24h: float
    low_24h: float
    bias: str
    confidence_score: int
    bias_summary: str
    trade_setup: Optional[TradeSetup] = None
    upcoming_high_impact_event: Optional[Dict[str, Any]] = None
    latest_geopolitical_headline: Optional[Dict[str, Any]] = None
    technical_snapshot: Dict[str, Any]
    disclaimer: str
    last_updated: datetime
