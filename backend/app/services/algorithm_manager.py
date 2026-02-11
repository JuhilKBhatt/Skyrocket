# backend/app/services/algorithm_manager.py
from sqlalchemy.orm import Session
from typing import List
from app.models.market_data import MarketCandle
from app.services.strategies import get_consensus_signal

def get_trade_decision(db: Session, ticker: str) -> str:
    """Live Decision: Fetches from DB and calls consensus logic."""
    recent_candles = db.query(MarketCandle).filter(
        MarketCandle.symbol == ticker,
        MarketCandle.timeframe == "30Min"
    ).order_by(MarketCandle.timestamp.desc()).limit(50).all()

    # Strategies expect ASC order for rolling calcs
    return get_decision_from_candles(recent_candles[::-1])

def get_decision_from_candles(candles: List[MarketCandle]) -> str:
    """Backtest Decision: Processes a pre-provided list of candles."""
    return get_consensus_signal(candles)