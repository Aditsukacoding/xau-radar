import sys
import os
import asyncio

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import engine, Base, SessionLocal
from app.services.ingestion_service import IngestionService
from app.services.technical_calc import TechnicalCalculator
from app.services.analysis_service import AnalysisService
from app.models.instrument import Instrument
from app.models.economic_event import EconomicEvent
from app.models.news_article import NewsArticle
from app.models.price_candle import PriceCandle
from app.models.analysis_report import AnalysisReport


async def run_tests():
    print("==================================================")
    print("Testing Trading Analytics Backend...")
    print("==================================================")

    # 1. Initialize Tables
    print("\n[1/6] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 2. Seed Data
    print("[2/6] Seeding initial data via IngestionService...")
    await IngestionService.seed_initial_data_if_empty(db)

    # 3. Verify Instrument
    print("[3/6] Verifying Instruments...")
    instruments = db.query(Instrument).all()
    assert len(instruments) > 0, "No instruments found!"
    print(f"  -> Found {len(instruments)} instrument(s): {[i.symbol for i in instruments]}")

    # 4. Verify Technical Calculator
    print("[4/6] Verifying Technical Indicator Calculations...")
    candles = db.query(PriceCandle).filter(PriceCandle.symbol == "XAUUSD", PriceCandle.timeframe == "1h").all()
    assert len(candles) >= 20, f"Expected at least 20 candles, got {len(candles)}"
    candles_dict = [
        {"open": c.open, "high": c.high, "low": c.low, "close": c.close, "volume": c.volume, "timestamp": c.timestamp}
        for c in candles
    ]
    tech = TechnicalCalculator.calculate_indicators(candles_dict)
    print(f"  -> Latest Price: ${tech['latest_price']}")
    print(f"  -> Trend: {tech['trend_direction']}")
    print(f"  -> RSI (14): {tech['rsi_14']} ({tech['rsi_condition']})")
    print(f"  -> SMA 20: ${tech['sma_20']} | SMA 50: ${tech['sma_50']}")
    print(f"  -> Support Levels: {tech['support_levels']}")
    print(f"  -> Resistance Levels: {tech['resistance_levels']}")
    assert tech["rsi_14"] is not None, "RSI calculation failed"

    # 5. Verify Analysis Report
    print("[5/6] Verifying Analysis Engine Synthesis...")
    report = await AnalysisService.get_or_generate_analysis(db, symbol="XAUUSD")
    assert report is not None, "Report generation failed"
    print(f"  -> Bias: {report.bias} ({report.confidence_score}% confidence)")
    print(f"  -> Summary: {report.summary}")
    print(f"  -> Mandatory Disclaimer: {report.disclaimer[:60]}...")
    assert "BUKAN" in report.disclaimer, "Disclaimer missing or incorrect"

    # 6. Verify FastAPI App Routes
    print("[6/6] Verifying FastAPI Endpoint Responses...")
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    res_root = client.get("/")
    assert res_root.status_code == 200, f"Root returned {res_root.status_code}"
    print("  -> GET / [OK 200]")

    res_summary = client.get("/api/v1/dashboard/summary/XAUUSD")
    assert res_summary.status_code == 200, f"Summary returned {res_summary.status_code}: {res_summary.text}"
    summary_data = res_summary.json()
    print(f"  -> GET /api/v1/dashboard/summary/XAUUSD [OK 200] (Bias: {summary_data['bias']}, Conf: {summary_data['confidence_score']}%)")

    res_calendar = client.get("/api/v1/fundamental/calendar")
    assert res_calendar.status_code == 200, f"Calendar returned {res_calendar.status_code}"
    print(f"  -> GET /api/v1/fundamental/calendar [OK 200] ({len(res_calendar.json())} events)")

    res_news = client.get("/api/v1/geopolitical/news?symbol=XAUUSD")
    assert res_news.status_code == 200, f"News returned {res_news.status_code}"
    print(f"  -> GET /api/v1/geopolitical/news [OK 200] ({len(res_news.json())} articles)")

    res_tech = client.get("/api/v1/technical/indicators/XAUUSD?timeframe=1h")
    assert res_tech.status_code == 200, f"Technical returned {res_tech.status_code}"
    print(f"  -> GET /api/v1/technical/indicators/XAUUSD [OK 200] (Trend: {res_tech.json()['trend_direction']})")

    res_candles = client.get("/api/v1/technical/candles/XAUUSD?timeframe=1h&limit=20")
    assert res_candles.status_code == 200, f"Candles returned {res_candles.status_code}"
    print(f"  -> GET /api/v1/technical/candles/XAUUSD [OK 200] ({len(res_candles.json())} candles)")

    db.close()
    print("\n==================================================")
    print("ALL BACKEND VERIFICATION CHECKS PASSED SUCCESSFULLY! ")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_tests())
