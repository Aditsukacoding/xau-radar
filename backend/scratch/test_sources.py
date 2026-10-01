import httpx
from datetime import datetime, timezone, timedelta
import json

now = datetime.now(timezone.utc)
from_date = (now - timedelta(days=2)).strftime('%Y-%m-%dT00:00:00.000Z')
to_date = (now + timedelta(days=7)).strftime('%Y-%m-%dT23:59:59.000Z')

print(f"Checking window: {from_date} to {to_date}")

# 1. TradingView
print("\n--- 1. Testing TradingView Economic Calendar ---")
tv_url = f"https://economic-calendar.tradingview.com/events?from={from_date}&to={to_date}"
tv_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Origin": "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/",
}
try:
    r = httpx.get(tv_url, headers=tv_headers, timeout=8.0)
    print("TradingView Status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        result = data.get("result", [])
        print(f"TradingView events: {len(result)}")
        acts = [e for e in result if e.get("actual") is not None]
        print(f"Events with ACTUAL: {len(acts)}")
        for e in acts[:5]:
            print(f"  [{e.get('country')}] {e.get('title')} -> Act: {e.get('actual')} | Frc: {e.get('forecast')} | Prv: {e.get('previous')}")
except Exception as e:
    print("TradingView error:", e)

# 2. Investing.com
print("\n--- 2. Testing Investing.com Economic Calendar ---")
try:
    inv_url = "https://api.investing.com/api/financialdata/assets/economicCalendar/events"
    # or mobile investing endpoint
    r2 = httpx.get(inv_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5.0)
    print("Investing.com status:", r2.status_code)
except Exception as e:
    print("Investing.com error:", e)

# 3. Finnhub (free tier, has calendar endpoint)
print("\n--- 3. Testing Finnhub / Yahoo Finance ---")
# Yahoo finance has an economic calendar:
yq_url = "https://query1.finance.yahoo.com/v1/finance/calendar/economic"
try:
    r3 = httpx.get(yq_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5.0)
    print("Yahoo Economic Calendar status:", r3.status_code)
except Exception as e:
    print("Yahoo error:", e)
