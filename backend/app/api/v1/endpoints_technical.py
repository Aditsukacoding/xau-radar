from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.price_candle import PriceCandle
from app.schemas.price_candle import PriceCandleResponse, TechnicalIndicatorsResponse
from app.services.technical_calc import TechnicalCalculator
from app.providers import get_data_provider

router = APIRouter()


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
    Auto-fetches from live provider if candles are missing or insufficient.
    """
    symbol = symbol.upper()
    tf = timeframe.lower()

    candles = (
        db.query(PriceCandle)
        .filter(PriceCandle.symbol == symbol, PriceCandle.timeframe == tf)
        .order_by(desc(PriceCandle.timestamp))
        .limit(limit)
        .all()
    )

    # Check if we need fresh live candles from provider
    need_refresh = False
    if not candles or len(candles) < 20:
        need_refresh = True
    else:
        # If latest candle is older than 30 minutes, refresh with live feed
        latest_time = candles[0].timestamp
        now_utc = datetime.now(timezone.utc)
        if latest_time.tzinfo is None:
            latest_time = latest_time.replace(tzinfo=timezone.utc)
        if (now_utc - latest_time).total_seconds() > 1800:
            need_refresh = True

    if need_refresh:
        provider = get_data_provider()
        raw_candles = await provider.get_price_candles(symbol=symbol, timeframe=tf, count=limit)
        for c in raw_candles:
            existing = (
                db.query(PriceCandle)
                .filter(
                    PriceCandle.symbol == symbol,
                    PriceCandle.timeframe == tf,
                    PriceCandle.timestamp == c["timestamp"],
                )
                .first()
            )
            if not existing:
                db.add(PriceCandle(
                    symbol=symbol,
                    timeframe=tf,
                    timestamp=c["timestamp"],
                    open=c["open"],
                    high=c["high"],
                    low=c["low"],
                    close=c["close"],
                    volume=c["volume"],
                ))
            else:
                existing.open = c["open"]
                existing.close = c["close"]
                existing.high = max(existing.high, c["high"])
                existing.low = min(existing.low, c["low"])
        db.commit()

        candles = (
            db.query(PriceCandle)
            .filter(PriceCandle.symbol == symbol, PriceCandle.timeframe == tf)
            .order_by(desc(PriceCandle.timestamp))
            .limit(limit)
            .all()
        )

    if not candles:
        raise HTTPException(
            status_code=404,
            detail=f"No candlestick data available for symbol '{symbol}' on timeframe '{timeframe}'"
        )

    # Return sorted ascending by time for charting libraries
    candles_sorted = sorted(candles, key=lambda c: c.timestamp)
    if candles_sorted:
        provider = get_data_provider()
        try:
            price_info = await provider.get_latest_price(symbol)
            curr_p = price_info.get("current_price")
            if curr_p and curr_p > 500.0:
                last_c = candles_sorted[-1]
                last_c.close = curr_p
                last_c.high = max(last_c.high, curr_p)
                last_c.low = min(last_c.low, curr_p)
        except Exception:
            pass

    return candles_sorted


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

    candles = (
        db.query(PriceCandle)
        .filter(PriceCandle.symbol == symbol, PriceCandle.timeframe == tf)
        .order_by(PriceCandle.timestamp.asc())
        .all()
    )

    if not candles or len(candles) < 20:
        provider = get_data_provider()
        raw_candles = await provider.get_price_candles(symbol=symbol, timeframe=tf, count=80)
        for c in raw_candles:
            existing = (
                db.query(PriceCandle)
                .filter(
                    PriceCandle.symbol == symbol,
                    PriceCandle.timeframe == tf,
                    PriceCandle.timestamp == c["timestamp"],
                )
                .first()
            )
            if not existing:
                db.add(PriceCandle(
                    symbol=symbol,
                    timeframe=tf,
                    timestamp=c["timestamp"],
                    open=c["open"],
                    high=c["high"],
                    low=c["low"],
                    close=c["close"],
                    volume=c["volume"],
                ))
            else:
                existing.open = c["open"]
                existing.close = c["close"]
                existing.high = max(existing.high, c["high"])
                existing.low = min(existing.low, c["low"])
        db.commit()

        candles = (
            db.query(PriceCandle)
            .filter(PriceCandle.symbol == symbol, PriceCandle.timeframe == tf)
            .order_by(PriceCandle.timestamp.asc())
            .all()
        )

    if not candles or len(candles) < 20:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient candle history for '{symbol}' to calculate technical indicators."
        )

    candles_list = [
        {"open": c.open, "high": c.high, "low": c.low, "close": c.close, "volume": c.volume, "timestamp": c.timestamp}
        for c in candles
    ]

    try:
        price_info = await provider.get_latest_price(symbol)
        curr_p = price_info.get("current_price")
        if curr_p and curr_p > 500.0 and candles_list:
            candles_list[-1]["close"] = curr_p
            candles_list[-1]["high"] = max(candles_list[-1]["high"], curr_p)
            candles_list[-1]["low"] = min(candles_list[-1]["low"], curr_p)
    except Exception:
        pass

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
