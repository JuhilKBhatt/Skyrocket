# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import settings
from app.routers import settings as settings_router, trades as trades_router, backtest as backtest_router
from app.core.database import SessionLocal
from app.services.market_data import update_all_watchlists, backfill_missing_candles
from app.services.trade_manager import run_trade_cycle

# SCHEDULER SETUP
scheduler = AsyncIOScheduler()

def scheduled_market_update():
    """Wrapper to create a DB session for the scheduled task"""
    print("⏰ Scheduler: Triggering market data update...")
    db = SessionLocal()
    try:
        update_all_watchlists(db)
        run_trade_cycle(db)
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. RUN BACKFILLER ON STARTUP
    print("🚀 App Startup: Running data gap filler...")
    db = SessionLocal()
    try:
        backfill_missing_candles(db)
    except Exception as e:
        print(f"⚠️ Backfill failed on startup: {e}")
    finally:
        db.close()

    # 2. START THE REGULAR SCHEDULED UPDATER
    print("⏰ Starting Scheduler...")
    scheduler.add_job(
        scheduled_market_update,
        'cron',
        minute='0,30',
        id='market_update',
        replace_existing=True
    )
    scheduler.start()
    yield
    print("🛑 Stopping Scheduler...")
    scheduler.shutdown()

# APP INITIALIZATION
app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

origins = [
    "http://localhost:5173", # Dev
    "http://localhost:80",   # Prod
    "http://localhost",      # (Standard)
    "http://127.0.0.1"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(settings_router.router)
app.include_router(trades_router.router)
app.include_router(backtest_router.router)