import httpx
from datetime import datetime, timezone, timedelta
import json

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
data = r.json()
result = data.get("result", [])

print(f"Total: {len(result)}")
if result:
    print("\nKeys:", list(result[0].keys()))
    print("\nFull sample event:")
    print(json.dumps(result[0], indent=2))

# Check major countries (US, EU, GB, JP, AU, CA)
major = [e for e in result if e.get("country") in ["US", "EU", "GB", "JP", "AU", "CA"]]
print(f"\nMajor currency events: {len(major)}")

# Check High impact events
# TradingView uses 'importance' usually: -1 (low), 0 (none), 1 (high) or similar
importances = set(e.get("importance") for e in major)
print("Unique importances:", importances)

# Check HIGH importance
high = [e for e in major if e.get("importance") == 1 or e.get("importance") == 2 or e.get("importance") == "high"]
print(f"High importance in major: {len(high)}")
for ev in high[:10]:
    date_str = ev.get("date")
    print(f"[{ev.get('country')}] {ev.get('title')} | Date: {date_str} | Act: {ev.get('actual')} | Frc: {ev.get('forecast')} | Prv: {ev.get('previous')} | Imp: {ev.get('importance')}")
