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
        target_event_title=event_title
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
