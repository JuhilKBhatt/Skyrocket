# backend/app/services/bot/runner.py
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.settings import GlobalSettings, Watchlist
from app.models.trade import Trade, TradeStatus

from .data_fetcher import get_latest_data
from .state_manager import StrategyState
from .strategy_logic import check_for_signals
from .execution import has_open_positions, execute_trade, trading_client
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

def check_and_close_open_trades(db, current_price):
    """Monitors open trades and closes them if SL/TP targets are hit."""
    open_trades = db.query(Trade).filter(Trade.status == TradeStatus.OPEN).all()
    
    for trade in open_trades:
        # We temporarily stored the TP in 'pnl' and SL in 'pnl_percent'
        tp_target = trade.pnl
        sl_target = trade.pnl_percent
        
        close_trade = False
        
        if trade.side == "BUY":
            if current_price >= tp_target or current_price <= sl_target:
                close_trade = True
                exit_side = OrderSide.SELL
        elif trade.side == "SELL":
            if current_price <= tp_target or current_price >= sl_target:
                close_trade = True
                exit_side = OrderSide.BUY

        if close_trade:
            print(f"🚨 Closing Trade ID {trade.id}: Target Hit @ {current_price}")
            try:
                # Send closing Market Order
                req = MarketOrderRequest(
                    symbol=trade.symbol.replace("/", ""),
                    qty=trade.quantity,
                    side=exit_side,
                    time_in_force=TimeInForce.GTC
                )
                trading_client.submit_order(req)
                
                # Update DB record
                trade.status = TradeStatus.CLOSED
                trade.exit_price = current_price
                trade.exit_time = datetime.now(timezone.utc)
                
                # Calculate real PNL
                if trade.side == "BUY":
                    trade.pnl = (current_price - trade.entry_price) * trade.quantity
                    trade.pnl_percent = ((current_price - trade.entry_price) / trade.entry_price) * 100
                else:
                    trade.pnl = (trade.entry_price - current_price) * trade.quantity
                    trade.pnl_percent = ((trade.entry_price - current_price) / trade.entry_price) * 100
                
                db.commit()
                print(f"✅ Trade Closed. PNL: ${trade.pnl:.2f}")
                
            except Exception as e:
                print(f"❌ Error closing trade: {e}")

def run_bot_iteration():
    print(f"\n--- 🤖 Running 15m Strategy Check: {datetime.now(timezone.utc).strftime('%H:%M UTC')} ---")
    
    db = SessionLocal()
    try:
        settings = db.query(GlobalSettings).first()
        if not settings or not settings.is_trading_enabled:
            print("💤 Trading is disabled in UI. Skipping.")
            return
            
        active_ticker = db.query(Watchlist).filter(Watchlist.is_active == True).first()
        if not active_ticker:
            print("⚠️ No active tickers in watchlist.")
            return
            
        symbol = active_ticker.ticker

        df = get_latest_data(symbol)
        if df.empty:
            print(f"⚠️ No data returned for {symbol}.")
            return
            
        latest_close_price = df.iloc[-1]['close']

        # --- NEW: Check exits before looking for new entries ---
        check_and_close_open_trades(db, latest_close_price)

        if has_open_positions(symbol):
            print(f"⏳ Open position exists for {symbol}. Monitoring targets.")
            return

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

        latest_candle = {
            'open': df.iloc[-1]['open'],
            'high': df.iloc[-1]['high'],
            'low': df.iloc[-1]['low'],
            'close': df.iloc[-1]['close'],
            'HA_Open': df.iloc[-1]['HA_Open'],
            'HA_Close': df.iloc[-1]['HA_Close']
        }

        signal = check_for_signals(bot_state, latest_candle)

        if signal != "NONE":
            # Pass db session to execute_trade so it can log the entry
            execute_trade(signal, latest_candle['close'], bot_state, settings, symbol, db)
        else:
            print(f"👀 Scanning {symbol}... Range: [${bot_state.range_low} - ${bot_state.range_high}]. No entry conditions met.")

    except Exception as e:
        print(f"❌ Bot Iteration Error: {e}")
    finally:
        db.close()