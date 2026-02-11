# backend/app/services/backtester.py
from sqlalchemy.orm import Session
from app.models.market_data import MarketCandle
from app.services.strategies import get_combined_signal
from typing import Dict

def run_backtest(db: Session, ticker: str, timeframe: str = "30Min") -> Dict:
    candles = db.query(MarketCandle).filter(
        MarketCandle.symbol == ticker,
        MarketCandle.timeframe == timeframe
    ).order_by(MarketCandle.timestamp.asc()).all()

    if len(candles) < 30:
        return {"error": "Insufficient data"}

    trades = []
    active_position = None
    balance = 10000.0
    initial_balance = 10000.0
    
    for i in range(20, len(candles)):
        current_candle = candles[i]
        
        # Determine if this is the last candle of the trading day
        is_eod = False
        if i < len(candles) - 1:
            next_candle = candles[i+1]
            if next_candle.timestamp.date() > current_candle.timestamp.date():
                is_eod = True
        else:
            is_eod = True # End of all data

        # Get signal
        history_slice_desc = candles[max(0, i-50):i+1][::-1]
        decision = get_combined_signal(history_slice_desc)

        # ENTRY: Only buy if it's not the end of the day
        if decision == "BUY" and not active_position and not is_eod:
            active_position = {
                "ticker": ticker,
                "entry_price": current_candle.close,
                "entry_time": current_candle.timestamp.isoformat(),
            }
        
        # EXIT: Sell on signal OR End of Day (Day Trading rule)
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