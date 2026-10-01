import requests

r = requests.get('http://localhost:8000/api/v1/fundamental/calendar?days=14')
data = r.json()
print('Total returned:', len(data))
with_actual = [x for x in data if x.get('actual_value')]
print('With actual value:', len(with_actual))
for x in with_actual[:10]:
    curr = x.get('currency')
    title = x.get('event_title')
    sched = x.get('scheduled_at')
    act = x.get('actual_value')
    fc = x.get('forecast_value')
    prv = x.get('previous_value')
    print(f"  [{curr}] {title} ({sched}) -> Actual: {act} | Forecast: {fc} | Prev: {prv}")
