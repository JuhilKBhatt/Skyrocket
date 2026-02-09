# backend/app/routers/trades.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.trade import Trade, TradeStatus
from app.models.market_data import MarketCandle
from app.schemas import TradeSchema, DashboardStats
from typing import List

router = APIRouter(prefix="/api/trades", tags=["trades"])

@router.get("/active", response_model=List[TradeSchema])
def get_active_trades(db: Session = Depends(get_db)):
    return db.query(Trade).filter(Trade.status == TradeStatus.OPEN).all()

@router.get("/history", response_model=List[TradeSchema])
def get_trade_history(db: Session = Depends(get_db)):
    return db.query(Trade).filter(Trade.status == TradeStatus.CLOSED).order_by(Trade.exit_time.desc()).limit(20).all()

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    # Calculate Total Investment (Current Value of Open Positions)
    active_trades = db.query(Trade).filter(Trade.status == TradeStatus.OPEN).all()
    
    total_val = 0
    for trade in active_trades:
        # Get latest price for the symbol
        latest = db.query(MarketCandle.close).filter(
            MarketCandle.symbol == trade.symbol
        ).order_by(MarketCandle.timestamp.desc()).first()
        
        price = latest[0] if latest else trade.entry_price
        total_val += (price * trade.quantity)

    # Placeholder for daily changes (can be calculated from historical PnL)
    return {
        "total_investment": round(total_val, 2),
        "day_change_pct": 0.52, 
        "yesterday_change_pct": 1.2
    }