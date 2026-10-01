from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime, timezone
from app.core.database import Base


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(16), index=True, nullable=False)
    timeframe = Column(String(8), default="1h")
    bias = Column(String(16), nullable=False)  # BULLISH, BEARISH, NEUTRAL
    confidence_score = Column(Integer, nullable=False)  # 0 to 100
    summary = Column(Text, nullable=False)
    fundamental_notes = Column(Text, nullable=True)
    geopolitical_notes = Column(Text, nullable=True)
    technical_notes = Column(Text, nullable=True)
    key_levels_json = Column(Text, nullable=True)  # JSON string of support & resistance
    trade_setup_json = Column(Text, nullable=True)  # JSON string of Entry, TP1, TP2, SL
    risk_factors_json = Column(Text, nullable=True)  # JSON string array of risks
    sources_json = Column(Text, nullable=True)  # JSON string array of evidence sources
    disclaimer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
