from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from datetime import datetime, timezone
from app.core.database import Base


class TradeSignalHistory(Base):
    """
    Persistent signal ledger tracking every XAU/USD Sniper Key-Zone entry
    (both LIVE generated setups and authentic 14-day candle-verified structural replays)
    against real OHLC price action to record exact SL / TP1 / TP2 / TP3 outcomes.
    """
    __tablename__ = "trade_signal_history"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False, default="XAUUSD")
    source_type = Column(String(20), nullable=False, default="LIVE")  # LIVE | AUDIT_14D

    action = Column(String(10), nullable=False)  # BUY | SELL
    action_label = Column(String(64), nullable=False, default="")
    execution_type = Column(String(16), nullable=False, default="LIMIT")  # LIMIT | INSTANT

    entry_zone = Column(String(64), nullable=False, default="")
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit_1 = Column(Float, nullable=False)
    take_profit_2 = Column(Float, nullable=False)
    take_profit_3 = Column(Float, nullable=False)

    risk_pips = Column(Float, nullable=False, default=40.0)
    reward_tp1_pips = Column(Float, nullable=False, default=60.0)
    reward_tp2_pips = Column(Float, nullable=False, default=110.0)
    reward_tp3_pips = Column(Float, nullable=False, default=170.0)

    setup_quality_score = Column(Integer, nullable=False, default=78)
    mtf_alignment = Column(String(100), nullable=True, default="")
    zone_proof = Column(Text, nullable=True, default="")
    session_name = Column(String(64), nullable=True, default="")

    # Real candle-verified lifecycle & outcome
    # PENDING_LIMIT | ACTIVE | TP1_HIT | TP2_HIT | TP3_HIT | SL_HIT | EXPIRED
    outcome = Column(String(24), nullable=False, default="PENDING_LIMIT", index=True)
    is_closed = Column(Boolean, nullable=False, default=False, index=True)

    triggered_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    hit_price = Column(Float, nullable=True)

    max_favorable_pips = Column(Float, nullable=False, default=0.0)
    max_adverse_pips = Column(Float, nullable=False, default=0.0)
    realized_pips = Column(Float, nullable=False, default=0.0)

    outcome_note = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
