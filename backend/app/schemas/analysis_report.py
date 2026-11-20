from pydantic import BaseModel, ConfigDict, field_serializer
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


class KeyLevels(BaseModel):
    support: List[float] = []
    resistance: List[float] = []


class TradeSetup(BaseModel):
    action: str = "WAIT"  # BUY, SELL, WAIT
    action_label: str = "WAIT / STANDBY"  # e.g. BUY NOW (SCALP), SELL LIMIT (PULLBACK)
    execution_type: str = "INSTANT"  # INSTANT, LIMIT, WAIT
    scalp_timeframe: str = "M1–D1 MTF"
    session_name: str = ""
    atr_pips: float = 0.0
    mtf_alignment: str = ""  # e.g. "6/7 BEARISH • Selaras Kuat"
    mtf_overview: List[Dict[str, Any]] = []  # All 7 TFs: M1, M5, M15, M30, H1, H4, D1
    confluence_note: str = ""  # Cross-timeframe zone comparison summary
    setup_quality_score: int = 78  # 0-100 structural zone quality score (not win rate)
    zone_proof: str = ""  # Concrete candle touch/rejection & TF confluence evidence
    zone_distance_pips: float = 0.0  # Distance from current spot to limit zone in pips
    entry_zone: str = ""  # e.g. $3554.80 - $3556.50
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    take_profit_3: float = 0.0
    risk_reward_ratio: str = "1 : 2.5"
    risk_pips: float = 0.0
    reward_tp1_pips: float = 0.0
    reward_tp2_pips: float = 0.0
    reward_tp3_pips: float = 0.0
    lot_management: str = "40% TP1 (SL→BEP) • 40% TP2 (SL→TP1) • 20% Runner TP3"
    entry_reasons: List[Dict[str, str]] = []  # 4 structured bullet reasons: Arah 7-TF, Zona Entry, SL Ketat, Target TP1-TP3
    technical_rationale: str = ""
    invalidation_level: str = ""
    status: str = "ACTIVE"  # ACTIVE, RUNNING_TP1_HIT, RUNNING_TP2_HIT, COMPLETED, STOPPED_OUT
    status_message: str = "Setup Scalping Aktif (Siap Eksekusi)"


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

    @field_serializer("created_at")
    def serialize_created_at_utc(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

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

    @field_serializer("last_updated")
    def serialize_last_updated_utc(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
