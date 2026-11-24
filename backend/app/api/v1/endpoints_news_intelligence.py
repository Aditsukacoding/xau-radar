from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.news_intelligence import NewsIntelligenceResponse
from app.services.news_intelligence_service import NewsIntelligenceService

router = APIRouter()


@router.get("/latest/{symbol}", response_model=NewsIntelligenceResponse)
async def get_latest_news_scenario(
    symbol: str = "XAUUSD",
    event_title: Optional[str] = Query(None, description="Judul event spesifik (misal: NFP, CPI, FOMC)"),
    currency: Optional[str] = Query(None, description="Mata uang event (misal: USD, GBP, EUR)"),
    scheduled_at: Optional[str] = Query(None, description="ISO timestamp jadwal event yang diklik"),
    forecast: Optional[str] = Query(None, description="Angka forecast/konsensus resmi dari kartu kalender"),
    previous: Optional[str] = Query(None, description="Angka rilis sebelumnya resmi dari kartu kalender"),
    actual: Optional[str] = Query(None, description="Angka aktual resmi jika sudah rilis"),
    db: Session = Depends(get_db)
):
    """
    Mengambil analisis skenario berita mendalam berdasarkan metodologi 9 langkah:
    - Rezim pasar saat ini & buktinya
    - Jalur transmisi geopolitik
    - Positioning COT & ETF
    - Kondisi chart multi-timeframe H4 / M30 / M5 & level invalidasi
    - Tiga skenario terukur: Kuat, Sesuai Konsensus, Lemah
    - Daftar katalis tertunda & jam rilis WIB
    """
    return await NewsIntelligenceService.get_or_generate_scenario(
        db=db,
        symbol=symbol.upper(),
        target_event_title=event_title,
        target_currency=currency,
        target_scheduled_at=scheduled_at,
        target_forecast=forecast,
        target_previous=previous,
        target_actual=actual,
    )


@router.post("/analyze/{symbol}", response_model=NewsIntelligenceResponse)
async def analyze_news_scenario(
    symbol: str = "XAUUSD",
    event_title: Optional[str] = Query(None, description="Judul event yang ingin dianalisis"),
    db: Session = Depends(get_db)
):
    """
    Memicu kalkulasi ulang analisis skenario berita secara real-time.
    """
    return await NewsIntelligenceService.get_or_generate_scenario(
        db=db,
        symbol=symbol.upper(),
        target_event_title=event_title
    )
