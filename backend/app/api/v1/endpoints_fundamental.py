from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.economic_event import EconomicEvent
from app.providers import get_data_provider
from app.services.tradingview_calendar_service import TradingViewCalendarService

router = APIRouter()


def _ev_to_dict(ev: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """Convert raw provider event dict to API response dict."""
    sched: datetime = ev["scheduled_at"]
    if sched.tzinfo is None:
        sched = sched.replace(tzinfo=timezone.utc)
    return {
        "id": idx,
        "external_id": ev.get("external_id"),
        "currency": ev.get("currency", "USD"),
        "event_title": ev.get("event_title", ""),
        "impact_level": ev.get("impact_level", "LOW"),
        "scheduled_at": sched.astimezone(timezone.utc).isoformat(),
        "actual_value": ev.get("actual_value"),
        "forecast_value": ev.get("forecast_value"),
        "previous_value": ev.get("previous_value"),
        "unit": ev.get("unit", ""),
        "sentiment_impact": ev.get("sentiment_impact", "NEUTRAL"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _orm_to_dict(ev: EconomicEvent, idx: int) -> Dict[str, Any]:
    """Convert SQLAlchemy ORM object to API response dict (same shape)."""
    sched = ev.scheduled_at
    if sched is None:
        sched = datetime.now(timezone.utc)
    if sched.tzinfo is None:
        sched = sched.replace(tzinfo=timezone.utc)
    created = ev.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return {
        "id": ev.id,
        "external_id": ev.external_id,
        "currency": ev.currency or "USD",
        "event_title": ev.event_title or "",
        "impact_level": ev.impact_level or "LOW",
        "scheduled_at": sched.astimezone(timezone.utc).isoformat(),
        "actual_value": ev.actual_value,
        "forecast_value": ev.forecast_value,
        "previous_value": ev.previous_value,
        "unit": ev.unit or "",
        "sentiment_impact": ev.sentiment_impact or "NEUTRAL",
        "created_at": (created.isoformat() if created else datetime.now(timezone.utc).isoformat()),
    }


async def _sync_ff_to_db(raw_events: list, db: Session):
    """Persist/upsert ForexFactory events into DB for offline fallback."""
    for ev in raw_events:
        ext_id = ev.get("external_id")
        if not ext_id:
            continue
        existing = db.query(EconomicEvent).filter(EconomicEvent.external_id == ext_id).first()
        if not existing:
            db.add(EconomicEvent(
                external_id=ext_id,
                currency=ev.get("currency", "USD"),
                event_title=ev.get("event_title", ""),
                impact_level=ev.get("impact_level", "LOW"),
                scheduled_at=ev.get("scheduled_at"),
                actual_value=ev.get("actual_value"),
                forecast_value=ev.get("forecast_value"),
                previous_value=ev.get("previous_value"),
                unit=ev.get("unit", ""),
                sentiment_impact=ev.get("sentiment_impact", "NEUTRAL"),
            ))
        else:
            # Update mutable fields
            changed = False
            for field, new_val in [
                ("actual_value", ev.get("actual_value")),
                ("forecast_value", ev.get("forecast_value")),
                ("previous_value", ev.get("previous_value")),
                ("impact_level", ev.get("impact_level")),
            ]:
                if new_val is not None and getattr(existing, field) != new_val:
                    setattr(existing, field, new_val)
                    changed = True
    try:
        db.commit()
    except Exception:
        db.rollback()


@router.get("/calendar")
async def get_economic_calendar(
    impact: Optional[str] = Query(None, description="Filter by impact: HIGH, MEDIUM, LOW"),
    currency: Optional[str] = Query(None, description="Filter by currency: USD, EUR, GBP, AUD..."),
    days: int = Query(14, description="Number of days ahead to view"),
    db: Session = Depends(get_db),
):
    """
    Real-time economic calendar from ForexFactory.

    Strategy:
    1. Try ForexFactory live provider (in-memory cache, 15-min TTL)
    2. If rate-limited / empty, fall back to DB (which was populated on last successful FF fetch)

    Times are UTC; Flutter converts to WIB (UTC+7) for display.
    """
    provider = get_data_provider()
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=2)
    end_date = now + timedelta(days=days)

    # --- Strategy 1: Live ForexFactory provider ---
    raw_events = await provider.get_economic_calendar(days_ahead=days)

    if raw_events:
        # Load actual values known in DB to enrich live feed
        db_actuals = {
            r[0]: r[1]
            for r in db.query(EconomicEvent.external_id, EconomicEvent.actual_value)
            .filter(EconomicEvent.actual_value.isnot(None), EconomicEvent.actual_value != "")
            .all()
        }

        # Persist to DB in background for fallback (non-blocking)
        try:
            await _sync_ff_to_db(raw_events, db)
        except Exception:
            pass

        results = []
        for idx, ev in enumerate(raw_events):
            sched: datetime = ev["scheduled_at"]
            if sched.tzinfo is None:
                sched = sched.replace(tzinfo=timezone.utc)
            if sched < start_date or sched > end_date:
                continue
            if impact and ev.get("impact_level", "").upper() != impact.upper():
                continue
            if currency and ev.get("currency", "").upper() != currency.upper():
                continue
            # Enrich actual_value if provider didn't have it
            if not ev.get("actual_value") and ev.get("external_id") in db_actuals:
                ev["actual_value"] = db_actuals[ev["external_id"]]
            results.append(_ev_to_dict(ev, idx + 1))

        # Real-time automatic enrichment from TradingView
        results = await TradingViewCalendarService.enrich_events_with_actuals(results)
        return results

    # --- Strategy 2: DB fallback (last successful FF fetch) ---
    query = db.query(EconomicEvent).filter(
        EconomicEvent.scheduled_at >= start_date,
        EconomicEvent.scheduled_at <= end_date,
        # Only serve real FF data — exclude mock events
        EconomicEvent.external_id.like("ff_%"),
    )
    if impact:
        query = query.filter(EconomicEvent.impact_level == impact.upper())
    if currency:
        query = query.filter(EconomicEvent.currency == currency.upper())

    db_events = query.order_by(EconomicEvent.scheduled_at.asc()).all()
    results = [_orm_to_dict(ev, idx + 1) for idx, ev in enumerate(db_events)]
    results = await TradingViewCalendarService.enrich_events_with_actuals(results)
    return results


@router.get("/upcoming-high-impact")
async def get_upcoming_high_impact(
    hours_ahead: int = Query(48, description="Upcoming hours window"),
    db: Session = Depends(get_db),
):
    """HIGH impact events within the next N hours — from ForexFactory (live or DB fallback)."""
    provider = get_data_provider()
    now = datetime.now(timezone.utc)
    until = now + timedelta(hours=hours_ahead)

    raw_events = await provider.get_economic_calendar(days_ahead=7)

    if raw_events:
        results = []
        for idx, ev in enumerate(raw_events):
            if ev.get("impact_level", "").upper() != "HIGH":
                continue
            sched: datetime = ev["scheduled_at"]
            if sched.tzinfo is None:
                sched = sched.replace(tzinfo=timezone.utc)
            if sched < now or sched > until:
                continue
            results.append(_ev_to_dict(ev, idx + 1))
        results = await TradingViewCalendarService.enrich_events_with_actuals(results)
        return results

    # DB fallback
    db_events = db.query(EconomicEvent).filter(
        EconomicEvent.impact_level == "HIGH",
        EconomicEvent.scheduled_at >= now,
        EconomicEvent.scheduled_at <= until,
        EconomicEvent.external_id.like("ff_%"),
    ).order_by(EconomicEvent.scheduled_at.asc()).all()
    results = [_orm_to_dict(ev, idx + 1) for idx, ev in enumerate(db_events)]
    results = await TradingViewCalendarService.enrich_events_with_actuals(results)
    return results


@router.post("/calendar/sync")
async def trigger_calendar_sync(db: Session = Depends(get_db)):
    """
    Force an immediate re-fetch from ForexFactory and sync real-time actuals from TradingView.
    Returns all events for the next 14 days.
    """
    from app.providers.live_provider import LiveDataProvider

    # Reset all caches so next call goes to network
    LiveDataProvider._calendar_cache = []
    LiveDataProvider._calendar_cache_time = 0.0
    LiveDataProvider._ff_retry_after_ts = 0.0

    # Sync real-time actuals from TradingView into DB
    await TradingViewCalendarService.sync_actuals_to_db(db)

    provider = get_data_provider()
    raw_events = await provider.get_economic_calendar(days_ahead=14)

    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=2)

    if raw_events:
        db_actuals = {
            r[0]: r[1]
            for r in db.query(EconomicEvent.external_id, EconomicEvent.actual_value)
            .filter(EconomicEvent.actual_value.isnot(None), EconomicEvent.actual_value != "")
            .all()
        }
        await _sync_ff_to_db(raw_events, db)
        results = []
        for idx, ev in enumerate(raw_events):
            if ev["scheduled_at"] >= start_date:
                if not ev.get("actual_value") and ev.get("external_id") in db_actuals:
                    ev["actual_value"] = db_actuals[ev["external_id"]]
                results.append(_ev_to_dict(ev, idx + 1))
        results = await TradingViewCalendarService.enrich_events_with_actuals(results)
        return results

    # Fallback: return whatever is in DB (last successful fetch)
    db_events = db.query(EconomicEvent).filter(
        EconomicEvent.scheduled_at >= start_date,
        EconomicEvent.external_id.like("ff_%"),
    ).order_by(EconomicEvent.scheduled_at.asc()).all()
    results = [_orm_to_dict(ev, idx + 1) for idx, ev in enumerate(db_events)]
    results = await TradingViewCalendarService.enrich_events_with_actuals(results)
    return results
