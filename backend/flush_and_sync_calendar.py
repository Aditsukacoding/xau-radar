import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.economic_event import EconomicEvent
from app.providers.live_provider import LiveDataProvider

async def main():
    # 1. Hapus semua economic events dari DB
    db = SessionLocal()
    try:
        count = db.query(EconomicEvent).count()
        print(f"Events di DB sebelum: {count}")
        db.query(EconomicEvent).delete()
        db.commit()
        print("OK: Semua data kalender di DB dihapus.")
    finally:
        db.close()

    # 2. Reset ForexFactory in-memory cache
    LiveDataProvider._calendar_cache = []
    LiveDataProvider._calendar_cache_time = 0.0
    LiveDataProvider._ff_retry_after_ts = 0.0
    print("OK: Cache ForexFactory di-reset.")

    # 3. Force fetch dari ForexFactory
    print("Fetching data real dari ForexFactory...")
    provider = LiveDataProvider()
    events = await provider.get_economic_calendar(days_ahead=14)

    if events:
        print(f"Berhasil ambil {len(events)} events dari ForexFactory!")
        high = [e for e in events if e.get('impact_level') == 'HIGH']
        print(f"  HIGH impact: {len(high)} events")
        print("\nContoh HIGH events:")
        for ev in high[:5]:
            from datetime import timedelta
            sched = ev['scheduled_at']
            wib = sched + timedelta(hours=7)
            fmt = wib.strftime('%a %d %b %Y %H:%M WIB')
            curr = ev['currency']
            title = ev['event_title']
            actual = ev.get('actual_value') or 'Belum rilis'
            fc = ev.get('forecast_value') or '-'
            print(f"  [{curr}] {title}")
            print(f"    WIB: {fmt}")
            print(f"    Aktual: {actual} | Forecast: {fc}")
    else:
        print("ForexFactory rate-limited (429) - coba lagi dalam 5 menit.")

asyncio.run(main())
