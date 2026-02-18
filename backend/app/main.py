# backend/app/main.py
import os
import sys
import subprocess
from datetime import datetime, time
from pytz import timezone # pip install pytz
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from huggingface_hub import login

from app.core.config import settings
from app.routers import settings as settings_router, trades as trades_router
from app.core.database import SessionLocal
from app.services.market_data import update_all_watchlists, backfill_missing_candles

# SCHEDULER SETUP
scheduler = AsyncIOScheduler()

# GLOBAL VARIABLE TO TRACK THE BOT PROCESS
bot_process = None

def start_trading_bot():
    """Launches the live_runner.py script as a subprocess"""
    global bot_process
    if bot_process and bot_process.poll() is None:
        print("⚠️ Trading Bot is already running.")
        return

    print("🚀 Market Open: Starting Trading Bot (live_runner.py)...")
    try:
        # ADD "-u" HERE: This forces unbuffered output so you see logs instantly
        bot_process = subprocess.Popen(
            [sys.executable, "-u", "app/services/live_runner.py"],
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True
        )
    except Exception as e:
        print(f"❌ Failed to start trading bot: {e}")

def stop_trading_bot():
    """Terminates the trading bot subprocess"""
    global bot_process
    if bot_process and bot_process.poll() is None:
        print("🛑 Market Close: Stopping Trading Bot...")
        bot_process.terminate()
        try:
            bot_process.wait(timeout=5) # Wait for graceful exit
        except subprocess.TimeoutExpired:
            bot_process.kill() # Force kill if stuck
    else:
        print("💤 Trading Bot is already stopped.")
    bot_process = None

def scheduled_market_update():
    """Wrapper to create a DB session for the scheduled task"""
    print("⏰ Scheduler: Triggering market data update...")
    db = SessionLocal()
    try:
        update_all_watchlists(db)
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. HUGGING FACE LOGIN
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        print("🤗 Hugging Face: Logging in...")
        login(token=hf_token)
    else:
        print("⚠️ Hugging Face: No token found. Rate limits may apply.")

    # 2. RUN BACKFILLER ON STARTUP
    print("🚀 App Startup: Running data gap filler...")
    db = SessionLocal()
    try:
        backfill_missing_candles(db)
    except Exception as e:
        print(f"⚠️ Backfill failed on startup: {e}")
    finally:
        db.close()

    # 3. SCHEDULE MARKET HOURS (New York Time)
    ny_tz = timezone('America/New_York')
    
    # Start at 9:30 AM ET (Mon-Fri)
    scheduler.add_job(
        start_trading_bot, 
        'cron', 
        day_of_week='mon-fri', 
        hour=9, 
        minute=30, 
        timezone=ny_tz,
        id='bot_start'
    )

    # Stop at 4:00 PM ET (Mon-Fri)
    scheduler.add_job(
        stop_trading_bot, 
        'cron', 
        day_of_week='mon-fri', 
        hour=16, 
        minute=0, 
        timezone=ny_tz,
        id='bot_stop'
    )

    # 4. IMMEDIATE STATUS CHECK
    # If the server restarts in the middle of the trading day, start the bot now.
    now = datetime.now(ny_tz)
    market_open = time(9, 30)
    market_close = time(16, 0)
    is_weekday = now.weekday() < 5 # 0=Mon, 4=Fri

    if is_weekday and market_open <= now.time() < market_close:
        print("📈 Market is currently OPEN. Starting bot immediately...")
        start_trading_bot()
    else:
        print("💤 Market is CLOSED. Bot scheduled for next open.")

    # 5. START DATA UPDATER SCHEDULER
    print("⏰ Starting Scheduler...")
    scheduler.add_job(
        scheduled_market_update,
        'cron',
        minute='0,30',
        id='market_update',
        replace_existing=True
    )
    scheduler.start()
    
    yield # App runs here
    
    # SHUTDOWN LOGIC
    print("🛑 App Shutdown: Stopping services...")
    stop_trading_bot() # Ensure bot doesn't become a zombie process
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