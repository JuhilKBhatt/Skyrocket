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

# Import our native bot runner
from app.services.bot.runner import run_bot_iteration

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Hugging Face
    hf_token = os.getenv("HF_TOKEN")
    if hf_token: login(token=hf_token)

    ny_tz = timezone('America/New_York')

    # 2. SCHEDULE THE TRADING BOT (Runs 24/7 every 15 minutes)
    scheduler.add_job(
        run_bot_iteration,
        'cron',
        minute='0,15,30,45',
        timezone=ny_tz,
        id='trading_bot_loop',
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(settings_router.router)
app.include_router(trades_router.router)