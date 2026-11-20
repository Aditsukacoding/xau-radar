import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.analysis_report import AnalysisReport
from app.schemas.analysis_report import AnalysisReportResponse, KeyLevels, TradeSetup
from app.services.analysis_service import AnalysisService

router = APIRouter()


def _format_report_response(report: AnalysisReport) -> AnalysisReportResponse:
    key_levels_raw = json.loads(report.key_levels_json) if report.key_levels_json else {}
    risk_factors_raw = json.loads(report.risk_factors_json) if report.risk_factors_json else []
    sources_raw = json.loads(report.sources_json) if report.sources_json else []
    trade_setup_raw = json.loads(report.trade_setup_json) if getattr(report, 'trade_setup_json', None) else None
    trade_setup_obj = TradeSetup(**trade_setup_raw) if trade_setup_raw else None

    return AnalysisReportResponse(
        id=report.id,
        symbol=report.symbol,
        timeframe=report.timeframe,
        bias=report.bias,
        confidence_score=report.confidence_score,
        summary=report.summary,
        fundamental_notes=report.fundamental_notes,
        geopolitical_notes=report.geopolitical_notes,
        technical_notes=report.technical_notes,
        key_levels=KeyLevels(
            support=key_levels_raw.get("support", []),
            resistance=key_levels_raw.get("resistance", []),
        ),
        trade_setup=trade_setup_obj,
        risk_factors=risk_factors_raw,
        sources=sources_raw,
        disclaimer=report.disclaimer,
        created_at=report.created_at,
    )


@router.get("/latest/{symbol}", response_model=AnalysisReportResponse)
async def get_latest_analysis_report(symbol: str = "XAUUSD", db: Session = Depends(get_db)):
    """
    Get the active locked setup & market bias report for an instrument (strictly locked until SL/TP).
    """
    symbol = symbol.upper()
    report = await AnalysisService.get_or_generate_analysis(db, symbol=symbol, force_refresh=False)
    return _format_report_response(report)


@router.post("/generate/{symbol}", response_model=AnalysisReportResponse)
async def trigger_fresh_analysis(
    symbol: str = "XAUUSD",
    force: bool = Query(False, description="Set true only to manually override a locked setup"),
    db: Session = Depends(get_db),
):
    """
    Checks live SL/TP progression on the locked setup. Only generates a brand-new setup if
    the locked setup has hit SL/TP/Expired, or if force=true is explicitly requested.
    """
    symbol = symbol.upper()
    report = await AnalysisService.get_or_generate_analysis(db, symbol=symbol, force_refresh=force)
    return _format_report_response(report)
