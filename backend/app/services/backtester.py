# backend/app/services/backtester.py
from sqlalchemy.orm import Session
from app.models.market_data import MarketCandle
from app.services.algorithm_manager import get_decision_from_candles
from typing import Dict

def run_backtest(db: Session, ticker: str, timeframe: str = "30Min") -> Dict:
    candles = db.query(MarketCandle).filter(
        MarketCandle.symbol == ticker,
        MarketCandle.timeframe == timeframe
    ).order_by(MarketCandle.timestamp.asc()).all()

    if len(candles) < 50: # Increased threshold for technical indicators
        return {"error": f"Insufficient data: {len(candles)} candles found."}

    trades = []
    active_position = None
    balance = 10000.0
    initial_balance = 10000.0
    
    for i in range(30, len(candles)):
        current_candle = candles[i]
        
        # Day Trading Exit Check
        is_eod = False
        if i < len(candles) - 1:
            if candles[i+1].timestamp.date() > current_candle.timestamp.date():
                is_eod = True
        else:
            is_eod = True

        # Call Algorithm Manager for decision
        # We provide the slice of history leading up to 'now'
        history_slice = candles[max(0, i-100):i+1]
        decision = get_decision_from_candles(history_slice)

        # Execution Logic
        if decision == "BUY" and not active_position and not is_eod:
            active_position = {
                "ticker": ticker,
                "entry_price": current_candle.close,
                "entry_time": current_candle.timestamp.isoformat(),
            }
        
        elif active_position and (decision == "SELL" or is_eod):
            exit_price = current_candle.close
            pnl_pct = (exit_price - active_position["entry_price"]) / active_position["entry_price"]
            pnl_amt = balance * pnl_pct
            
            balance += pnl_amt
            trades.append({
                **active_position,
                "exit_price": exit_price,
                "exit_time": current_candle.timestamp.isoformat(),
                "pnl": round(pnl_amt, 2),
                "pnl_percent": round(pnl_pct * 100, 2),
                "exit_reason": "EOD" if is_eod else "SIGNAL"
            })
            active_position = None

    return {
        "ticker": ticker,
        "summary": {
            "initial_balance": initial_balance,
            "final_balance": round(balance, 2),
            "total_return_pct": round(((balance - initial_balance) / initial_balance) * 100, 2),
            "total_trades": len(trades),
            "win_rate": round(len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100, 2) if trades else 0
        },
        "trades": trades,
        "chart_data": [{"time": c.timestamp.isoformat(), "price": c.close} for c in candles]
    }