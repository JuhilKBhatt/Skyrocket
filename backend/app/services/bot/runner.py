# backend/app/services/bot/runner.py
from datetime import datetime
from app.core.database import SessionLocal
from app.models.settings import GlobalSettings, Watchlist

from .data_fetcher import get_latest_data
from .state_manager import StrategyState
from .strategy_logic import check_for_signals
from .execution import has_open_positions, execute_trade

# Global state persists as long as the FastAPI server is running
bot_state = StrategyState()

def run_bot_iteration():
    print(f"\n--- 🤖 Running 15m Strategy Check: {datetime.utcnow().strftime('%H:%M UTC')} ---")
    
    db = SessionLocal()
    try:
        # 1. Fetch live UI Settings
        settings = db.query(GlobalSettings).first()
        if not settings or not settings.is_trading_enabled:
            print("💤 Trading is disabled in UI. Skipping.")
            return
            
        active_ticker = db.query(Watchlist).filter(Watchlist.is_active == True).first()
        if not active_ticker:
            print("⚠️ No active tickers in watchlist.")
            return
            
        symbol = active_ticker.ticker

        # 2. Check if we are already in a trade
        if has_open_positions(symbol):
            print(f"⏳ Open position exists for {symbol}. Letting Bracket Order work.")
            return

        # 3. Fetch Data & Build HA
        df = get_latest_data(symbol)
        if df.empty:
            print(f"⚠️ No data returned for {symbol}.")
            return

        latest_candle = df.iloc[-1]
        current_time = latest_candle.name # Timestamp

        # 4. Update Strategy State
        bot_state.update_state(current_time, latest_candle)

        # 5. Check for Signal
        signal = check_for_signals(bot_state, latest_candle)

        # 6. Execute
        if signal != "NONE":
            execute_trade(signal, latest_candle['close'], bot_state, settings, symbol)
        else:
            print("👀 Scanning... No entry conditions met.")

    except Exception as e:
        print(f"❌ Bot Iteration Error: {e}")
    finally:
        db.close()