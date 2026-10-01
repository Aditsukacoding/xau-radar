"""
Simpan data ForexFactory yang sudah ada di in-memory cache ke DB,
agar endpoint GET /calendar bisa serve data real (bukan mock, bukan kosong).
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.economic_event import EconomicEvent
from app.providers.live_provider import LiveDataProvider

async def main():
    provider = LiveDataProvider()

    # Fetch dari ForexFactory (gunakan cache yang sudah ada, JANGAN hit network lagi)
    cache = LiveDataProvider._calendar_cache
    print(f"Events in in-memory cache: {len(cache)}")

    if not cache:
        print("Cache kosong - mencoba fetch ulang dari ForexFactory...")
        # Paksa fetch
        LiveDataProvider._calendar_cache_time = 0.0
        LiveDataProvider._ff_retry_after_ts = 0.0
        events = await provider.get_economic_calendar(days_ahead=14)
        cache = events
        print(f"Setelah fetch: {len(cache)} events")

    if not cache:
        print("Masih kosong. ForexFactory masih rate-limited.")
        print("Tunggu 5 menit lagi lalu jalankan script ini.")
        return

    # Simpan ke DB
    db = SessionLocal()
    try:
        # Bersihkan dulu
        existing = db.query(EconomicEvent).count()
        if existing > 0:
            db.query(EconomicEvent).delete()
            db.commit()
            print(f"Dihapus {existing} events lama.")

        # Insert semua dari cache
        inserted = 0
        for ev in cache:
            db.add(EconomicEvent(
                external_id=ev.get("external_id"),
                currency=ev.get("currency", "USD"),
                event_title=ev.get("event_title", ""),
                impact_level=ev.get("impact_level", "LOW"),
                scheduled_at=ev.get("scheduled_at"),
                actual_value=ev.get("actual_value"),
                forecast_value=ev.get("forecast_value"),
                previous_value=ev.get("previous_value"),
                unit=ev.get("unit", ""),
                sentiment_impact=ev.get("sentiment_impact", "NEUTRAL"),
            ))
            inserted += 1

        db.commit()
        print(f"Tersimpan {inserted} events real ForexFactory ke DB.")

        # Verifikasi
        total = db.query(EconomicEvent).count()
        high = db.query(EconomicEvent).filter(EconomicEvent.impact_level == 'HIGH').count()
        print(f"DB sekarang: {total} total, {high} HIGH impact")

        # Tampilkan sample
        samples = db.query(EconomicEvent).filter(
            EconomicEvent.impact_level == 'HIGH'
        ).order_by(EconomicEvent.scheduled_at).limit(5).all()

        print("\nSample HIGH events di DB:")
        from datetime import timedelta
        for ev in samples:
            wib = ev.scheduled_at + timedelta(hours=7)
            fmt = wib.strftime('%a %d %b %Y %H:%M WIB')
            is_real = 'REAL FF' if ev.external_id and ev.external_id.startswith('ff_') else 'OTHER'
            print(f"  [{ev.currency}] {ev.event_title}")
            print(f"    WIB: {fmt} | {is_real}")
            actual = ev.actual_value or 'Belum rilis'
            print(f"    Forecast: {ev.forecast_value or '-'} | Actual: {actual}")

    finally:
        db.close()

asyncio.run(main())
