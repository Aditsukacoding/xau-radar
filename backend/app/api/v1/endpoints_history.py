from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.signal_history import SignalHistoryResponse
from app.services.signal_history_service import SignalHistoryService

router = APIRouter()


@router.get("/history/{symbol}", response_model=SignalHistoryResponse)
async def get_signal_history(
    symbol: str = "XAUUSD",
    action: str = Query("ALL", description="Filter direction: ALL, BUY, SELL"),
    outcome: str = Query("ALL", description="Filter outcome: ALL, WIN, LOSS, OPEN"),
    limit: int = Query(40, ge=5, le=80),
    db: Session = Depends(get_db),
):
    """
    Returns complete verified Signal History & SL/TP Outcome Ledger (WIB timestamps)
    with Win Rate, Net Pips, BUY vs SELL breakdown, and MFE/MAE candle tracking.
    """
    return await SignalHistoryService.get_history_response(
        db=db,
        symbol=symbol.upper(),
        action_filter=action,
        outcome_filter=outcome,
        limit=limit,
    )


@router.post("/refresh/{symbol}", response_model=SignalHistoryResponse)
async def refresh_signal_history(
    symbol: str = "XAUUSD",
    db: Session = Depends(get_db),
):
    """Forces re-evaluation of all active/pending signals against latest real candles & spot."""
    return await SignalHistoryService.get_history_response(
        db=db,
        symbol=symbol.upper(),
        action_filter="ALL",
        outcome_filter="ALL",
        limit=40,
    )
