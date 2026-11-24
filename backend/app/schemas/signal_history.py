from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, field_serializer


class SignalHistoryItem(BaseModel):
    id: int
    symbol: str
    source_type: str  # LIVE | AUDIT_14D
    action: str  # BUY | SELL
    action_label: str
    execution_type: str
    entry_zone: str
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_pips: float
    reward_tp1_pips: float
    reward_tp2_pips: float
    reward_tp3_pips: float
    setup_quality_score: int
    mtf_alignment: str = ""
    zone_proof: str = ""
    session_name: str = ""
    outcome: str  # PENDING_LIMIT | ACTIVE | TP1_HIT | TP2_HIT | TP3_HIT | SL_HIT | EXPIRED
    is_closed: bool
    triggered_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    hit_price: Optional[float] = None
    max_favorable_pips: float = 0.0
    max_adverse_pips: float = 0.0
    realized_pips: float = 0.0
    outcome_note: str = ""
    post_mortem: Optional[Dict[str, Any]] = None
    created_at: datetime
    created_at_wib: str = ""
    triggered_at_wib: Optional[str] = None
    closed_at_wib: Optional[str] = None

    @field_serializer("created_at", "triggered_at", "closed_at")
    def serialize_utc_dt(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    model_config = ConfigDict(from_attributes=True)


class SignalHistoryStats(BaseModel):
    total_signals: int = 0
    closed_trades: int = 0
    active_or_pending: int = 0
    wins: int = 0
    losses: int = 0
    expired: int = 0
    tp1_hits: int = 0
    tp2_hits: int = 0
    tp3_hits: int = 0
    sl_hits: int = 0
    buy_count: int = 0
    sell_count: int = 0
    buy_wins: int = 0
    sell_wins: int = 0
    win_rate_pct: float = 0.0
    net_pips: float = 0.0
    avg_win_pips: float = 0.0
    avg_loss_pips: float = 0.0
    profit_factor: float = 0.0


class SignalHistoryResponse(BaseModel):
    symbol: str
    current_price: float
    updated_at_wib: str
    stats: SignalHistoryStats
    self_evaluation: Optional[Dict[str, Any]] = None
    items: List[SignalHistoryItem]
    methodology_note: str
