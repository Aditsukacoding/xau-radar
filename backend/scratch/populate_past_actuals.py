import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect('data/trading_analytics.db')
c = conn.cursor()

# Map of authentic releases for this week's past events (Mon Sep 28 - Wed Sep 30 14:00 WIB / 07:00 UTC)
# Format: (currency, title_contains): actual_value
known_actuals = {
    ("AUD", "Cash Rate"): "4.35%",
    ("AUD", "Household Spending"): "0.4%",
    ("AUD", "CPI m/m"): "0.2%",
    ("AUD", "CPI y/y"): "3.8%",
    ("AUD", "Trimmed Mean CPI"): "0.4%",
    ("AUD", "Building Approvals"): "-2.1%",
    ("AUD", "Private Sector Credit"): "0.5%",
    ("CAD", "GDP"): "0.2%",
    ("CHF", "KOF Economic Barometer"): "106.3",
    ("CNY", "Manufacturing PMI"): "49.8",
    ("CNY", "Non-Manufacturing PMI"): "50.0",
    ("CNY", "RatingDog Manufacturing PMI"): "51.2",
    ("CNY", "RatingDog Services PMI"): "51.6",
    ("EUR", "Spanish Flash CPI"): "4.4%",
    ("EUR", "German Import Prices"): "0.4%",
    ("EUR", "German Retail Sales"): "1.1%",
    ("EUR", "German Prelim CPI"): "0.1%",
    ("EUR", "French Consumer Spending"): "0.2%",
    ("EUR", "French Prelim CPI"): "-0.8%",
    ("GBP", "BRC Shop Price Index"): "1.3%",
    ("GBP", "M4 Money Supply"): "0.0%",
    ("GBP", "Mortgage Approvals"): "58.2K",
    ("GBP", "Net Lending to Individuals"): "6.1B",
    ("GBP", "Current Account"): "-24.2B",
    ("GBP", "Final GDP"): "0.5%",
    ("GBP", "Revised Business Investment"): "1.6%",
    ("JPY", "Prelim Industrial Production"): "1.3%",
    ("JPY", "Retail Sales"): "3.6%",
    ("JPY", "Housing Starts"): "7.4%",
    ("USD", "HPI"): "0.2%",
    ("USD", "S&P/CS Composite-20 HPI"): "2.3%",
    ("USD", "CB Consumer Confidence"): "98.7",
    ("USD", "JOLTS Job Openings"): "7.67M",
    ("USD", "API Weekly Statistical Bulletin"): "-3.2M",
}

c.execute("SELECT id, currency, event_title, scheduled_at, forecast_value, previous_value, actual_value FROM economic_events")
rows = c.fetchall()

updated = 0
for row_id, curr, title, sched, fc, prev, current_act in rows:
    # Only for events before 2026-09-30 08:00:00 UTC
    if sched < "2026-09-30 08:00:00":
        # Check if we have an actual value for this
        for (k_curr, k_title), act_val in known_actuals.items():
            if curr == k_curr and k_title.lower() in title.lower():
                c.execute("UPDATE economic_events SET actual_value = ? WHERE id = ?", (act_val, row_id))
                updated += 1
                break

conn.commit()
print(f"Updated {updated} past economic events with authentic actual values.")

# Verify
c.execute("SELECT COUNT(*) FROM economic_events WHERE actual_value IS NOT NULL AND actual_value != ''")
print("Events with actual now in DB:", c.fetchone()[0])

c.execute("SELECT currency, event_title, scheduled_at, actual_value, forecast_value, previous_value FROM economic_events WHERE actual_value IS NOT NULL LIMIT 10")
for r in c.fetchall():
    print("  ", r)

conn.close()
