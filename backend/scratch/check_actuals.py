import sqlite3

conn = sqlite3.connect('data/trading_analytics.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM economic_events')
print('Total in DB:', c.fetchone()[0])

c.execute('SELECT COUNT(*) FROM economic_events WHERE actual_value IS NOT NULL AND actual_value != ""')
print('With actual in DB:', c.fetchone()[0])

c.execute('SELECT currency, event_title, scheduled_at, actual_value, forecast_value, previous_value FROM economic_events ORDER BY scheduled_at ASC LIMIT 25')
rows = c.fetchall()
for row in rows:
    print(row)
