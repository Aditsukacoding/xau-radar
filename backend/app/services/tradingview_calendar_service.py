"""
TradingView Economic Calendar Enrichment Service.

Provides real-time automatic 'actual_value' matching and enrichment
for ForexFactory economic calendar events.
"""

import asyncio
import logging
import re
import difflib
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session

from app.models.economic_event import EconomicEvent

logger = logging.getLogger(__name__)


class TradingViewCalendarService:
    _tv_cache: List[Dict[str, Any]] = []
    _tv_cache_time: float = 0.0
    _CACHE_TTL: float = 60.0  # 1 minute

    # Currency to TradingView country mapping
    CURRENCY_COUNTRY_MAP = {
        "USD": {"US"},
        "EUR": {"EU", "DE", "FR", "IT", "ES"},
        "GBP": {"GB"},
        "JPY": {"JP"},
        "AUD": {"AU"},
        "CAD": {"CA"},
        "CHF": {"CH"},
        "CNY": {"CN"},
        "NZD": {"NZ"},
    }

    @classmethod
    def _normalize_title(cls, title: str) -> str:
        """Strip periodic indicators and noise for semantic matching."""
        t = title.lower()
        t = re.sub(r"\(.*?\)", "", t)
        t = re.sub(r"\b(m/m|y/y|q/q|mom|yoy|qoq|flash|prelim|final)\b", "", t)
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        return " ".join(t.split())

    @classmethod
    def _match_score(cls, ff_title: str, tv_title: str) -> float:
        """Calculate similarity score between ForexFactory title and TradingView title."""
        ff_lower = ff_title.lower()
        tv_lower = tv_title.lower()

        # Non-numeric events (speeches, meetings, statements) do not produce actual statistics
        non_numeric_kw = ["speaks", "statement", "press conference", "meeting minutes", "auction"]
        if any(k in ff_lower for k in non_numeric_kw):
            return 0.0

        # Frequency conflicts (e.g. m/m vs y/y)
        ff_has_mom = any(k in ff_lower for k in ["m/m", "mom", "month"])
        ff_has_yoy = any(k in ff_lower for k in ["y/y", "yoy", "year"])
        ff_has_qoq = any(k in ff_lower for k in ["q/q", "qoq", "quarter"])

        tv_has_mom = any(k in tv_lower for k in ["mom", "month"])
        tv_has_yoy = any(k in tv_lower for k in ["yoy", "year"])
        tv_has_qoq = any(k in tv_lower for k in ["qoq", "quarter"])

        if (ff_has_mom and tv_has_yoy) or (ff_has_yoy and tv_has_mom):
            return 0.0
        if (ff_has_qoq and (tv_has_mom or tv_has_yoy)) or ((ff_has_mom or ff_has_yoy) and tv_has_qoq):
            return 0.0

        n1 = cls._normalize_title(ff_title)
        n2 = cls._normalize_title(tv_title)
        if n1 == n2:
            return 1.0
        if n1 in n2 or n2 in n1:
            return 0.95

        s1 = set(n1.split())
        s2 = set(n2.split())
        if not s1 or not s2:
            return 0.0
        overlap = len(s1.intersection(s2)) / min(len(s1), len(s2))
        ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
        return max(overlap, ratio)

    @classmethod
    def _format_actual(cls, actual_val: Any, forecast: Optional[str], previous: Optional[str]) -> str:
        """Format raw TradingView number to match ForexFactory presentation."""
        if actual_val is None:
            return ""

        # Format float if needed
        if isinstance(actual_val, float):
            # If round number or up to 2 decimal places
            if actual_val.is_integer():
                act_str = f"{int(actual_val)}"
            else:
                act_str = f"{actual_val:.2f}".rstrip("0").rstrip(".")
        else:
            act_str = str(actual_val).strip()

        ref = (forecast or "") + " " + (previous or "")
        ref = ref.strip()

        # Append % if reference had %
        if "%" in ref and not act_str.endswith("%"):
            act_str += "%"
        # Append B if reference had B (billions)
        elif "B" in ref and not act_str.endswith("B"):
            act_str += "B"
        # Append M if reference had M (millions)
        elif "M" in ref and not act_str.endswith("M"):
            act_str += "M"
        # Append K if reference had K (thousands)
        elif "K" in ref and not act_str.endswith("K"):
            act_str += "K"

        return act_str

    @classmethod
    async def fetch_tradingview_events(cls, days_back: int = 3, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Fetch economic events from TradingView API with 60-second caching."""
        now_ts = time.time()
        if cls._tv_cache and (now_ts - cls._tv_cache_time) < cls._CACHE_TTL:
            return cls._tv_cache

        now = datetime.now(timezone.utc)
        from_date = (now - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00.000Z")
        to_date = (now + timedelta(days=days_ahead)).strftime("%Y-%m-%dT23:59:59.000Z")

        tv_url = f"https://economic-calendar.tradingview.com/events?from={from_date}&to={to_date}"
        tv_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Origin": "https://www.tradingview.com",
            "Referer": "https://www.tradingview.com/",
        }

        try:
            async with httpx.AsyncClient(headers=tv_headers, timeout=8.0) as client:
                r = await client.get(tv_url)
                if r.status_code == 200:
                    data = r.json()
                    result = data.get("result", [])
                    cls._tv_cache = result
                    cls._tv_cache_time = now_ts
                    logger.debug(f"Fetched {len(result)} events from TradingView Calendar.")
                    return result
                else:
                    logger.warning(f"TradingView Calendar HTTP {r.status_code}")
        except Exception as e:
            logger.warning(f"Failed to fetch TradingView Calendar: {e}")

        return cls._tv_cache or []

    @classmethod
    def match_actual_for_event(
        cls,
        currency: str,
        title: str,
        scheduled_at: datetime,
        forecast: Optional[str],
        previous: Optional[str],
        tv_events: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Find the matching actual value from TradingView events."""
        allowed_countries = cls.CURRENCY_COUNTRY_MAP.get(currency.upper(), set())
        allowed_countries.add(currency.upper()[:2])

        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

        best_tv = None
        best_score = 0.0

        for tv in tv_events:
            tv_act = tv.get("actual")
            if tv_act is None:
                continue

            # Check currency or country
            tv_curr = tv.get("currency", "").upper()
            tv_country = tv.get("country", "").upper()
            if tv_curr != currency.upper() and tv_country not in allowed_countries:
                continue

            # Time check within 4 hours
            tv_date_str = tv.get("date", "")
            try:
                tv_dt = datetime.fromisoformat(tv_date_str.replace("Z", "+00:00")).astimezone(timezone.utc)
            except Exception:
                continue

            time_diff = abs((tv_dt - scheduled_at).total_seconds())
            if time_diff > 14400:  # 4 hours
                continue

            tv_title = tv.get("title", "")
            score = cls._match_score(title, tv_title)
            if score > best_score:
                best_score = score
                best_tv = tv

        if best_tv and best_score >= 0.5:
            return cls._format_actual(best_tv.get("actual"), forecast, previous)

        return None

    @classmethod
    async def enrich_events_with_actuals(cls, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich a list of ForexFactory event dicts with real-time actual values from TradingView."""
        tv_events = await cls.fetch_tradingview_events()
        if not tv_events:
            return events

        for ev in events:
            # If already has actual, keep it
            if ev.get("actual_value") and str(ev["actual_value"]).strip():
                continue

            sched = ev.get("scheduled_at")
            if isinstance(sched, str):
                try:
                    sched = datetime.fromisoformat(sched)
                except Exception:
                    continue
            elif not isinstance(sched, datetime):
                continue

            act = cls.match_actual_for_event(
                currency=ev.get("currency", "USD"),
                title=ev.get("event_title", ""),
                scheduled_at=sched,
                forecast=ev.get("forecast_value"),
                previous=ev.get("previous_value"),
                tv_events=tv_events,
            )
            if act:
                ev["actual_value"] = act

        return events

    @classmethod
    async def sync_actuals_to_db(cls, db: Session) -> int:
        """Scan DB for past events with missing actual values and fill them from TradingView."""
        now = datetime.now(timezone.utc)
        tv_events = await cls.fetch_tradingview_events()
        if not tv_events:
            return 0

        pending_events = (
            db.query(EconomicEvent)
            .filter(
                EconomicEvent.scheduled_at <= now,
                (EconomicEvent.actual_value.is_(None) | (EconomicEvent.actual_value == "")),
            )
            .all()
        )

        updated_count = 0
        for ev in pending_events:
            act = cls.match_actual_for_event(
                currency=ev.currency,
                title=ev.event_title,
                scheduled_at=ev.scheduled_at,
                forecast=ev.forecast_value,
                previous=ev.previous_value,
                tv_events=tv_events,
            )
            if act:
                ev.actual_value = act
                updated_count += 1

        if updated_count > 0:
            try:
                db.commit()
                logger.info(f"[TradingView Sync] Updated {updated_count} actual values in DB.")
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to commit TradingView actuals sync: {e}")

        return updated_count
