import sqlite3

conn = sqlite3.connect('data/trading_analytics.db')
c = conn.cursor()
c.execute('SELECT currency, event_title, scheduled_at, forecast_value, previous_value, impact_level FROM economic_events WHERE scheduled_at < "2026-09-30 07:00:00"')
rows = c.fetchall()
print(f'Total past events: {len(rows)}')
for r in rows:
    print(r)
