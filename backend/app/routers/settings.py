# backend/app/routers/settings.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.settings import Watchlist, GlobalSettings
from app.schemas import WatchlistCreate, Watchlist as WatchlistSchema
from app.schemas import GlobalSettingsUpdate, GlobalSettings as GlobalSettingsSchema
from app.services.market_data import fetch_and_store_history

router = APIRouter(prefix="/api/settings", tags=["settings"])

# WATCHLIST ENDPOINTS
@router.get("/watchlist", response_model=List[WatchlistSchema])
def get_watchlist(db: Session = Depends(get_db)):
    return db.query(Watchlist).all()

@router.post("/watchlist", response_model=WatchlistSchema)
def add_company(company: WatchlistCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Check if exists
    exists = db.query(Watchlist).filter(Watchlist.ticker == company.ticker).first()
    if exists:
        raise HTTPException(status_code=400, detail="Ticker already in watchlist")
    
    new_item = Watchlist(**company.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    # Fetch historical data in background
    background_tasks.add_task(fetch_and_store_history, new_item.ticker, db)

    return new_item

@router.delete("/watchlist/{ticker}")
def remove_company(ticker: str, db: Session = Depends(get_db)):
    item = db.query(Watchlist).filter(Watchlist.ticker == ticker).first()
    if not item:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Deleted successfully"}

# GLOBAL SETTINGS ENDPOINTS
@router.get("/global", response_model=GlobalSettingsSchema)
def get_global_settings(db: Session = Depends(get_db)):
    settings = db.query(GlobalSettings).first()
    if not settings:
        # Create default if missing
        settings = GlobalSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.post("/global", response_model=GlobalSettingsSchema)
def update_global_settings(config: GlobalSettingsUpdate, db: Session = Depends(get_db)):
    settings = db.query(GlobalSettings).first()
    if not settings:
        settings = GlobalSettings()
        db.add(settings)
    
    settings.max_trade_allocation_pct = config.max_trade_allocation_pct
    settings.global_stop_loss_pct = config.global_stop_loss_pct
    settings.take_profit_pct = config.take_profit_pct
    settings.is_trading_enabled = config.is_trading_enabled
    
    db.commit()
    db.refresh(settings)
    return settings