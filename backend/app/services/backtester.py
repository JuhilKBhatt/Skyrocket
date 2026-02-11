# backend/app/services/backtester.py
from sqlalchemy.orm import Session
from app.models.market_data import MarketCandle
from app.services.strategies import get_combined_signal
from typing import Dict

def run_backtest(db: Session, ticker: str, timeframe: str = "30Min") -> Dict:
    # 1. Fetch historical data
    candles = db.query(MarketCandle).filter(
        MarketCandle.symbol == ticker,
        MarketCandle.timeframe == timeframe
    ).order_by(MarketCandle.timestamp.asc()).all()

    if len(candles) < 30:
        return {"error": "Insufficient data"}

    trades = []
    active_position = None
    balance = 10000.0
    
    # 2. Simulation Loop
    for i in range(20, len(candles)):
        current_candle = candles[i]
        history_slice_desc = candles[max(0, i-50):i+1][::-1]
        decision = get_combined_signal(history_slice_desc)

        if decision == "BUY" and not active_position:
            active_position = {
                "ticker": ticker,
                "entry_price": current_candle.close,
                "entry_time": current_candle.timestamp.isoformat(),
            }
        
        elif (decision == "SELL" or i == len(candles) - 1) and active_position:
            trades.append({
                **active_position,
                "exit_price": current_candle.close,
                "exit_time": current_candle.timestamp.isoformat(),
                "pnl_percent": ((current_candle.close - active_position["entry_price"]) / active_position["entry_price"]) * 100
            })
            active_position = None

    # 3. Return results PLUS candle data for the chart
    return {
        "ticker": ticker,
        "summary": {
            "total_trades": len(trades),
            "final_balance": balance, # (Add your balance calculation logic here)
        },
        "trades": trades,
        "chart_data": [
            {"time": c.timestamp.isoformat(), "price": c.close} for c in candles
        ]
    }