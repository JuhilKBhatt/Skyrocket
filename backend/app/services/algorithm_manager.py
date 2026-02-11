# backend/app/services/algorithm_manager.py
from sqlalchemy.orm import Session
from app.models.market_data import MarketCandle
from app.services.strategies import get_combined_signal

def get_trade_decision(db: Session, ticker: str) -> str:
    """Fetches data from DB and returns a consensus signal."""
    recent_candles = db.query(MarketCandle).filter(
        MarketCandle.symbol == ticker,
        MarketCandle.timeframe == "30Min"
    ).order_by(MarketCandle.timestamp.desc()).limit(50).all()

    if not recent_candles:
        return "HOLD"

    return get_combined_signal(recent_candles)