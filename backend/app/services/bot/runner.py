# backend/app/services/bot/runner.py
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.settings import GlobalSettings, Watchlist

from .data_fetcher import get_latest_data
from .state_manager import StrategyState
from .strategy_logic import check_for_signals
from .execution import has_open_positions, execute_trade

def run_bot_iteration():
    print(f"\n--- 🤖 Running 15m Strategy Check: {datetime.now(timezone.utc).strftime('%H:%M UTC')} ---")
    
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

        # 3. Fetch Data & Build HA (Fetches 4 days to ensure HA math is perfectly stabilized)
        df = get_latest_data(symbol)
        if df.empty:
            print(f"⚠️ No data returned for {symbol}.")
            return

        # 4. REBUILD STATE (Fixes the "Cold Start" bug)
        # By instantiating a fresh state and replaying the historical data,
        # the bot instantly learns the correct 4H ranges and HA trap states!
        bot_state = StrategyState()

        for timestamp, row in df.iterrows():
            candle = {
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'HA_Open': row['HA_Open'],
                'HA_Close': row['HA_Close']
            }
            bot_state.update_state(timestamp, candle)

        # 5. Check Logic on the VERY LAST closed candle only
        latest_candle = {
            'open': df.iloc[-1]['open'],
            'high': df.iloc[-1]['high'],
            'low': df.iloc[-1]['low'],
            'close': df.iloc[-1]['close'],
            'HA_Open': df.iloc[-1]['HA_Open'],
            'HA_Close': df.iloc[-1]['HA_Close']
        }

        signal = check_for_signals(bot_state, latest_candle)

        # 6. Execute
        if signal != "NONE":
            execute_trade(signal, latest_candle['close'], bot_state, settings, symbol)
        else:
            print(f"👀 Scanning {symbol}... Range: [${bot_state.range_low} - ${bot_state.range_high}]. No entry conditions met.")

    except Exception as e:
        print(f"❌ Bot Iteration Error: {e}")
    finally:
        db.close()