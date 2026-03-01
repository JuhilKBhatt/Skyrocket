# backend/app/main.py
import os
from datetime import datetime
from pytz import timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from huggingface_hub import login

from app.core.database import SessionLocal
from app.routers import settings as settings_router, trades as trades_router
from app.services.market_data import update_all_watchlists, backfill_missing_candles

# Import our new native bot runner!
from app.services.bot.runner import run_bot_iteration

scheduler = AsyncIOScheduler()

def scheduled_market_update():
    """Wrapper to create a DB session for the UI chart data fetcher"""
    db = SessionLocal()
    try:
        update_all_watchlists(db)
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Hugging Face
    hf_token = os.getenv("HF_TOKEN")
    if hf_token: login(token=hf_token)

    # 2. Startup Backfill
    db = SessionLocal()
    try:
        backfill_missing_candles(db)
    finally:
        db.close()

    ny_tz = timezone('America/New_York')

    # 3. SCHEDULE THE TRADING BOT (Runs 24/7 every 15 minutes)
    # Crypto markets never sleep, so this runs constantly on the 0, 15, 30, and 45 minute marks.
    scheduler.add_job(
        run_bot_iteration,
        'cron',
        minute='0,15,30,45',
        timezone=ny_tz,
        id='trading_bot_loop',
        replace_existing=True
    )

    # 4. SCHEDULE UI MARKET DATA FETCHING
    scheduler.add_job(
        scheduled_market_update,
        'cron',
        minute='*', # Fetches every minute for UI updates
        timezone=ny_tz,
        id='market_update_loop',
        replace_existing=True
    )

    print("⏰ Schedulers Started!")
    scheduler.start()
    
    yield
    
    print("🛑 App Shutdown: Stopping schedulers...")
    scheduler.shutdown()

# APP INITIALIZATION
PROJECT_NAME = os.getenv("PROJECT_NAME", "Skyrocket Trading Bot")
app = FastAPI(title=PROJECT_NAME, lifespan=lifespan)

origins = [
    "http://localhost:5173", 
    "http://localhost:80",   
    "http://localhost",      
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