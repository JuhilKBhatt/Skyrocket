# backend/app/services/live_runner.py
import os
import sys
from lumibot.brokers import Alpaca
from trading_bot import MLTrader

# Add parent directories to path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.models.settings import GlobalSettings, Watchlist

# --- CONFIGURATION ---
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_BASE_URL")

ALPACA_CREDS = {
    "API_KEY":API_KEY, 
    "API_SECRET": API_SECRET, 
    "PAPER": True
}

def run_live_trading():
    # 1. FETCH SETTINGS FROM DB
    # Defaults
    symbol = "SPY"
    cash_at_risk = 0.5
    take_profit = 0.10
    stop_loss = 0.05

    db = SessionLocal()
    try:
        # Get Risk Parameters
        settings = db.query(GlobalSettings).first()
        if settings:
            cash_at_risk = settings.max_trade_allocation_pct / 100.0
            take_profit = settings.take_profit_pct / 100.0
            stop_loss = settings.global_stop_loss_pct / 100.0
        
        # Get Active Symbol (Pick the first active one)
        ticker_item = db.query(Watchlist).filter(Watchlist.is_active == True).first()
        if ticker_item:
            symbol = ticker_item.ticker

        print(f"🚀 STARTING LIVE BOT")
        print(f"TARGET: {symbol}")
        print(f"RISK: {cash_at_risk:.0%} | TP: {take_profit:.0%} | SL: {stop_loss:.0%}")

    except Exception as e:
        print(f"⚠️ Error reading DB: {e}")
    finally:
        db.close()

    # 2. SETUP BROKER (Paper Trading)
    # Ensure "PAPER": True is in your ALPACA_CREDS inside trading_bot.py
    broker = Alpaca(ALPACA_CREDS)

    # 3. INITIALIZE STRATEGY
    strategy = MLTrader(
        name='mlstrat_live',
        broker=broker,
        parameters={
            "symbol": symbol,
            "cash_at_risk": cash_at_risk,
            "tp_pct": take_profit,
            "sl_pct": stop_loss
        }
    )

    # 4. RUN LIVE (Not Backtest)
    # This connects to the Alpaca WebSocket and waits for market updates
    strategy.run_live()

if __name__ == "__main__":
    run_live_trading()