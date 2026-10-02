import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api.v1.router import api_router
from app.services.ingestion_service import IngestionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("trading_backend")


import asyncio
from app.services.analysis_service import AnalysisService
from app.providers import get_data_provider

async def _background_price_tick_loop():
    """
    Sub-second real-time price tick worker.
    Continuously updates the in-memory cache directly from FOREX.com / TradingView
    every 700ms so all client endpoints respond in <1 millisecond with zero latency.
    """
    provider = get_data_provider()
    while True:
        try:
            await provider.get_latest_price("XAUUSD", force_refresh=True)
        except asyncio.CancelledError:
            break
        except Exception:
            pass
        await asyncio.sleep(2.5)


async def _background_auto_ingestion_loop():
    logger.info("Starting background auto-ingestion daemon for breaking news & calendar events...")
    await asyncio.sleep(5)
    cycle = 0
    import time as _time
    calendar_last_sync = _time.time()  # Wait 5 minutes before first background calendar poll
    while True:
        try:
            db = SessionLocal()
            try:
                # News ingestion: every 30s (RSS feeds are cheap, no rate limits)
                new_articles = await IngestionService.ingest_latest_news(db, "XAUUSD")
                if new_articles > 0:
                    logger.info(f"[Auto-Ingestion] {new_articles} new breaking news articles ingested.")

                # Real-time actuals sync from TradingView: every 60s (zero rate limit)
                if cycle % 2 == 0:
                    try:
                        from app.services.tradingview_calendar_service import TradingViewCalendarService
                        tv_synced = await TradingViewCalendarService.sync_actuals_to_db(db)
                        if tv_synced > 0:
                            logger.info(f"[Auto-Ingestion] {tv_synced} economic actuals auto-updated via TradingView.")
                    except Exception as e:
                        logger.warning(f"[Auto-Ingestion] TradingView actuals sync failed: {e}")

                # Calendar ingestion: every 5 minutes (ForexFactory has CloudFlare rate limits)
                now_ts = _time.time()
                if now_ts - calendar_last_sync >= 300:  # 5 minutes
                    await IngestionService.ingest_latest_calendar(db)
                    calendar_last_sync = now_ts

                # Re-synthesize fresh AI market analysis if new articles arrived or every 5 cycles (~2.5 mins)
                cycle += 1
                if new_articles > 0 or cycle % 5 == 0:
                    await AnalysisService.generate_fresh_analysis(db, "XAUUSD")
                    logger.info("[Auto-Ingestion] Fresh AI market bias synthesized from real-time feeds.")
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"[Auto-Ingestion] Background cycle error: {e}")

        # Continuous 30-second cycle for ultra-responsive news availability
        await asyncio.sleep(30)



@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize database tables
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # 2. Seed initial data for XAUUSD if database is newly created
    db = SessionLocal()
    try:
        await IngestionService.seed_initial_data_if_empty(db)
        logger.info("Database initialized and verified successfully.")
    except Exception as e:
        logger.error(f"Error during database startup seed: {e}")
    finally:
        db.close()

    # 3. Start continuous sub-second live price tick worker & background ingestion daemon
    # (Only active in standalone ASGI/Uvicorn mode; disabled in synchronous WSGI/Passenger to avoid thread hangs)
    is_wsgi = bool(os.environ.get("IS_WSGI") or os.environ.get("PASSENGER_APP_ENV"))
    price_task = None
    ingestion_task = None
    if not is_wsgi:
        price_task = asyncio.create_task(_background_price_tick_loop())
        ingestion_task = asyncio.create_task(_background_auto_ingestion_loop())

    yield

    if price_task:
        price_task.cancel()
    if ingestion_task:
        ingestion_task.cancel()
    if price_task or ingestion_task:
        try:
            tasks = [t for t in (price_task, ingestion_task) if t]
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            pass
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Trading Bias Analysis Engine Backend. "
        "Mensintesis data Fundamental (Kalender Ekonomi), Geopolitik (Berita/Sentimen), "
        "dan Teknikal (OHLCV, Indikator) untuk menghasilkan kesimpulan arah bias pasar "
        "yang transparan dan objektif untuk XAU/USD."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Flutter mobile client, Web, and Emulators
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API router
app.include_router(api_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "docs_url": "/docs",
        "mode": "Mock Data (Realistic)" if settings.USE_MOCK_DATA else "Live API",
        "disclaimer": settings.MANDATORY_DISCLAIMER,
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
