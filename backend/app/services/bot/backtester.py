# backend/app/services/bot/backtester.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone

# Import your exact live strategy logic!
from state_manager import StrategyState
from strategy_logic import check_for_signals

# --- BACKTEST PARAMETERS ---
SYMBOL = "BTC-USD"  # yfinance format
TIMEFRAME = "15m"
DAYS_BACK = 59      # yfinance max for 15m is 60 days
MAX_RISK_PCT = 0.5
RR_RATIO = 2.0
INITIAL_CAPITAL = 10000.0
TRADE_RISK_PCT = 0.02  # Risk 2% of capital per trade

def calculate_heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """Replicates the data_fetcher.py HA math"""
    ha_df = df.copy()
    ha_df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    
    ha_open = [df['Open'].iloc[0]]
    for i in range(1, len(df)):
        ha_open.append((ha_open[i-1] + ha_df['HA_Close'].iloc[i-1]) / 2)
    ha_df['HA_Open'] = ha_open
    
    ha_df['HA_High'] = ha_df[['High', 'HA_Open', 'HA_Close']].max(axis=1)
    ha_df['HA_Low'] = ha_df[['Low', 'HA_Open', 'HA_Close']].min(axis=1)
    return ha_df

def run_backtest():
    print(f"📥 Fetching {DAYS_BACK} days of {TIMEFRAME} data for {SYMBOL}...")
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=DAYS_BACK)
    
    raw_df = yf.download(SYMBOL, start=start_date, end=end_date, interval=TIMEFRAME, progress=False)
    if raw_df.empty:
        print("❌ Failed to fetch data.")
        return

    # Flatten yfinance multi-index if necessary
    if isinstance(raw_df.columns, pd.MultiIndex):
        raw_df.columns = raw_df.columns.droplevel(1)

    df = calculate_heikin_ashi(raw_df)
    
    bot_state = StrategyState()
    
    # Tracking Variables
    capital = INITIAL_CAPITAL
    open_trade = None
    trade_history = []
    
    print("🤖 Simulating Strategy...")

    # Loop through history candle by candle
    for timestamp, row in df.iterrows():
        # Standardize dictionary keys to match your live bot format
        candle = {
            'open': row['Open'], 'high': row['High'], 'low': row['Low'], 'close': row['Close'],
            'HA_Open': row['HA_Open'], 'HA_Close': row['HA_Close']
        }

        # 1. Manage Open Trade (Check if SL or TP hit)
        if open_trade:
            # Check for Stop Loss or Take Profit
            hit_sl = False
            hit_tp = False
            
            if open_trade['side'] == 'LONG':
                if candle['low'] <= open_trade['sl']: hit_sl = True
                elif candle['high'] >= open_trade['tp']: hit_tp = True
            elif open_trade['side'] == 'SHORT':
                if candle['high'] >= open_trade['sl']: hit_sl = True
                elif candle['low'] <= open_trade['tp']: hit_tp = True

            if hit_sl or hit_tp:
                exit_price = open_trade['sl'] if hit_sl else open_trade['tp']
                
                # Calculate Profit
                if open_trade['side'] == 'LONG':
                    profit = (exit_price - open_trade['entry']) * open_trade['qty']
                else:
                    profit = (open_trade['entry'] - exit_price) * open_trade['qty']
                
                capital += profit
                trade_history.append({
                    'side': open_trade['side'],
                    'entry_time': open_trade['entry_time'],
                    'exit_time': timestamp,
                    'profit': profit,
                    'result': 'WIN' if hit_tp else 'LOSS'
                })
                open_trade = None # Trade closed
            continue # Don't look for new setups while in a trade

        # 2. Update State
        bot_state.update_state(timestamp, candle)

        # 3. Check Logic
        signal = check_for_signals(bot_state, candle)

        # 4. Execute Entry
        if signal != "NONE":
            real_close = candle['close']
            
            # Risk Calculation
            if signal == "LONG":
                risk_amount = real_close - bot_state.ext_low
                sl_price = bot_state.ext_low
                tp_price = real_close + (risk_amount * RR_RATIO)
            else: # SHORT
                risk_amount = bot_state.ext_high - real_close
                sl_price = bot_state.ext_high
                tp_price = real_close - (risk_amount * RR_RATIO)

            if risk_amount <= 0: continue
            
            risk_pct = (risk_amount / real_close) * 100
            if risk_pct > MAX_RISK_PCT:
                bot_state.is_outside_down = False
                bot_state.is_outside_up = False
                continue

            # Position Sizing (Risking 2% of total capital)
            dollars_at_risk = capital * TRADE_RISK_PCT
            qty = dollars_at_risk / risk_amount
            
            open_trade = {
                'side': signal,
                'entry': real_close,
                'sl': sl_price,
                'tp': tp_price,
                'qty': qty,
                'entry_time': timestamp
            }
            
            # Reset Trap
            bot_state.is_outside_down = False
            bot_state.is_outside_up = False

    # --- PRINT RESULTS ---
    wins = [t for t in trade_history if t['result'] == 'WIN']
    losses = [t for t in trade_history if t['result'] == 'LOSS']
    win_rate = (len(wins) / len(trade_history) * 100) if trade_history else 0
    total_return = ((capital - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100

    print("\n" + "="*40)
    print("📊 BACKTEST RESULTS (60 Days)")
    print("="*40)
    print(f"Total Trades: {len(trade_history)}")
    print(f"Wins: {len(wins)} | Losses: {len(losses)}")
    print(f"Win Rate:     {win_rate:.2f}%")
    print(f"Start Cap:    ${INITIAL_CAPITAL:,.2f}")
    print(f"Final Cap:    ${capital:,.2f}")
    print(f"Total Return: {total_return:.2f}%")
    print("="*40)

if __name__ == "__main__":
    run_backtest()