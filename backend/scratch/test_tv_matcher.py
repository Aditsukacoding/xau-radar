import httpx
from datetime import datetime, timezone, timedelta
import re
import difflib

def normalize_title(title: str) -> str:
    """Normalize title for matching (remove frequency tags, lowercase, clean)."""
    t = title.lower()
    t = re.sub(r'\(.*?\)', '', t)  # remove parentheses
    t = re.sub(r'\b(m/m|y/y|q/q|mom|yoy|qoq|flash|prelim|final)\b', '', t)
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    return " ".join(t.split())

def match_score(t1: str, t2: str) -> float:
    n1 = normalize_title(t1)
    n2 = normalize_title(t2)
    if n1 == n2:
        return 1.0
    # Check if one is substring of other
    if n1 in n2 or n2 in n1:
        return 0.9
    # Token set overlap
    s1 = set(n1.split())
    s2 = set(n2.split())
    if not s1 or not s2:
        return 0.0
    overlap = len(s1.intersection(s2)) / min(len(s1), len(s2))
    diff = difflib.SequenceMatcher(None, n1, n2).ratio()
    return max(overlap, diff)

# Test with actual FF and TV data
now = datetime.now(timezone.utc)
from_date = (now - timedelta(days=2)).strftime('%Y-%m-%dT00:00:00.000Z')
to_date = (now + timedelta(days=7)).strftime('%Y-%m-%dT23:59:59.000Z')

tv_url = f"https://economic-calendar.tradingview.com/events?from={from_date}&to={to_date}"
tv_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Origin": "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/",
}

r = httpx.get(tv_url, headers=tv_headers, timeout=10.0)
tv_events = r.json().get("result", [])
print(f"Fetched {len(tv_events)} TradingView events.")

# Index TV events by (currency, date_bucket)
# date_bucket can be YYYY-MM-DD-HH or YYYY-MM-DD
tv_indexed = []
for ev in tv_events:
    act = ev.get("actual")
    if act is not None:
        try:
            dt = datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            continue
        curr = ev.get("currency")
        tv_indexed.append({
            "title": ev.get("title", ""),
            "indicator": ev.get("indicator", ""),
            "currency": curr,
            "country": ev.get("country", ""),
            "actual": act,
            "actual_raw": ev.get("actualRaw"),
            "forecast": ev.get("forecast"),
            "previous": ev.get("previous"),
            "dt": dt,
        })

print(f"TV events with actual: {len(tv_indexed)}")

# Test matching against our SQLite FF events
import sqlite3
conn = sqlite3.connect("data/trading_analytics.db")
c = conn.cursor()
c.execute("SELECT id, currency, event_title, scheduled_at, forecast_value, previous_value, actual_value FROM economic_events")
ff_rows = c.fetchall()

matched_count = 0
for row in ff_rows:
    row_id, ff_curr, ff_title, ff_sched, ff_fc, ff_prev, current_act = row
    try:
        ff_dt = datetime.fromisoformat(ff_sched).replace(tzinfo=timezone.utc)
    except Exception:
        continue

    # Find candidates in TV with same currency and within 4 hours
    best_candidate = None
    best_score = 0.0

    for tv in tv_indexed:
        if tv["currency"] != ff_curr:
            continue
        # Time difference within 3 hours
        time_diff = abs((tv["dt"] - ff_dt).total_seconds())
        if time_diff > 10800:  # 3 hours
            continue

        score = match_score(ff_title, tv["title"])
        if score > best_score:
            best_score = score
            best_candidate = tv

    if best_candidate and best_score >= 0.5:
        matched_count += 1
        act_str = str(best_candidate["actual"])
        # If forecast has %, add %
        if ff_fc and "%" in ff_fc and not act_str.endswith("%"):
            act_str += "%"
        elif ff_prev and "%" in ff_prev and not act_str.endswith("%"):
            act_str += "%"
        print(f"MATCH ({best_score:.2f}): FF '{ff_title}' ({ff_curr}) == TV '{best_candidate['title']}' -> ACT: {act_str}")

print(f"\nTotal matched FF events with TV actuals: {matched_count}/{len(ff_rows)}")
