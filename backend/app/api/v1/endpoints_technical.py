import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.price_candle import PriceCandle
from app.schemas.price_candle import PriceCandleResponse, TechnicalIndicatorsResponse
from app.services.technical_calc import TechnicalCalculator
from app.providers import get_data_provider

router = APIRouter()


async def _load_live_or_db_candles(
    db: Session,
    symbol: str,
    tf: str,
    count: int,
) -> List[Dict[str, Any]]:
    """
    Loads candles directly from the fast in-memory-cached LiveDataProvider (Yahoo/TwelveData)
    concurrently with live spot price (TradingView FOREX.com) and falls back to a single
    bounded DB query only if the external feed is unavailable. Avoids N+1 per-candle SQL
    writes inside GET endpoints so remote Neon PostgreSQL never bottlenecks serverless requests.
    """
    provider = get_data_provider()
    raw_res, price_res = await asyncio.gather(
        asyncio.wait_for(provider.get_price_candles(symbol=symbol, timeframe=tf, count=count), timeout=8.0),
        asyncio.wait_for(provider.get_latest_price(symbol), timeout=4.0),
        return_exceptions=True,
    )

    curr_p = 0.0
    if isinstance(price_res, dict):
        try:
            curr_p = float(price_res.get("current_price") or 0.0)
        except Exception:
            curr_p = 0.0

    candles_list: List[Dict[str, Any]] = []
    if isinstance(raw_res, list) and len(raw_res) >= 15:
        sorted_raw = sorted(raw_res, key=lambda c: c["timestamp"])
        candles_list = [dict(c) for c in sorted_raw]
    else:
        db_rows = (
            db.query(PriceCandle)
            .filter(PriceCandle.symbol == symbol, PriceCandle.timeframe == tf)
            .order_by(desc(PriceCandle.timestamp))
            .limit(count)
            .all()
        )
        candles_list = [
            {
                "id": c.id,
                "symbol": c.symbol,
                "timeframe": c.timeframe,
                "timestamp": c.timestamp,
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume or 0.0),
            }
            for c in reversed(db_rows)
        ]

    if candles_list and curr_p > 500.0:
        last_c = candles_list[-1]
        last_c["close"] = curr_p
        last_c["high"] = max(float(last_c["high"]), curr_p)
        last_c["low"] = min(float(last_c["low"]), curr_p)

    return candles_list


@router.get("/candles/{symbol}", response_model=List[PriceCandleResponse])
async def get_candlestick_chart_data(
    symbol: str = "XAUUSD",
    timeframe: str = Query("1h", description="Timeframe: 5m, 15m, 1h, 4h, 1d"),
    limit: int = Query(100, ge=10, le=500),
    db: Session = Depends(get_db),
):
    """
    Get OHLCV candlestick records for charting on mobile.
    Sorted chronologically (ascending timestamp).
    """
    symbol = symbol.upper()
    tf = timeframe.lower()

    candles_list = await _load_live_or_db_candles(db, symbol, tf, limit)
    if not candles_list:
        raise HTTPException(
            status_code=404,
            detail=f"No candlestick data available for symbol '{symbol}' on timeframe '{timeframe}'",
        )

    return [
        PriceCandleResponse(
            id=int(c.get("id") or (i + 1)),
            symbol=symbol,
            timeframe=tf,
            timestamp=c["timestamp"],
            open=float(c["open"]),
            high=float(c["high"]),
            low=float(c["low"]),
            close=float(c["close"]),
            volume=float(c.get("volume") or 0.0),
        )
        for i, c in enumerate(candles_list[-limit:])
    ]


@router.get("/live-price/{symbol}")
async def get_live_price_tick(symbol: str = "XAUUSD"):
    """
    High-frequency real-time price tick endpoint for dynamic candle updating.
    """
    provider = get_data_provider()
    return await provider.get_latest_price(symbol=symbol.upper())


@router.get("/indicators/{symbol}", response_model=TechnicalIndicatorsResponse)
async def get_technical_indicators(
    symbol: str = "XAUUSD",
    timeframe: str = Query("1h", description="Timeframe: 5m, 15m, 1h, 4h, 1d"),
    db: Session = Depends(get_db),
):
    """
    Get calculated technical indicators:
    - RSI (14) & Overbought/Oversold condition
    - Moving averages: SMA 20, 50, 200 and EMA 9, 21
    - Automatically detected Support and Resistance levels
    - Trend direction (BULLISH, BEARISH, SIDEWAYS)
    """
    symbol = symbol.upper()
    tf = timeframe.lower()

    candles_list = await _load_live_or_db_candles(db, symbol, tf, 220)
    if not candles_list or len(candles_list) < 20:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient candle history for '{symbol}' to calculate technical indicators.",
        )

    calc_res = TechnicalCalculator.calculate_indicators(candles_list)

    return TechnicalIndicatorsResponse(
        symbol=symbol,
        timeframe=timeframe,
        latest_price=calc_res["latest_price"],
        rsi_14=calc_res.get("rsi_14"),
        rsi_condition=calc_res.get("rsi_condition"),
        sma_20=calc_res.get("sma_20"),
        sma_50=calc_res.get("sma_50"),
        sma_200=calc_res.get("sma_200"),
        ema_9=calc_res.get("ema_9"),
        ema_21=calc_res.get("ema_21"),
        trend_direction=calc_res["trend_direction"],
        support_levels=calc_res["support_levels"],
        resistance_levels=calc_res["resistance_levels"],
        summary=calc_res["summary"],
    )
