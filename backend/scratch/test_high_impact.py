import requests
from datetime import datetime, timedelta

r = requests.get('http://localhost:8000/api/v1/fundamental/calendar?days=14&impact=HIGH')
data = r.json()
print(f"HIGH impact events: {len(data)}")
for ev in data:
    utc = datetime.fromisoformat(ev['scheduled_at'])
    wib = utc + timedelta(hours=7)
    curr = ev['currency']
    title = ev['event_title']
    act = ev['actual_value'] or 'Belum rilis'
    fc = ev['forecast_value'] or '-'
    prv = ev['previous_value'] or '-'
    time_str = wib.strftime("%a %d %b %H:%M WIB")
    print(f"[{curr}] {title}")
    print(f"   WIB: {time_str} | Actual: {act} | Forecast: {fc} | Prev: {prv}")
