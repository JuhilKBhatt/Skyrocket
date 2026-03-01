# backend/app/services/bot/backtester.py
import pandas as pd
import os
import sys
from datetime import datetime, timedelta, timezone

# Alpaca Imports
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Project Imports
from app.core.config import settings
from state_manager import StrategyState
from strategy_logic import check_for_signals

# --- BACKTEST PARAMETERS ---
SYMBOL = "BTC/USD"  # Changed to Alpaca's crypto format
TIMEFRAME_MINS = 15
DAYS_BACK = 60      # Alpaca doesn't have the strict 60-day limit for 15m like yfinance, you can increase this!
MAX_RISK_PCT = 0.5
RR_RATIO = 2.0
INITIAL_CAPITAL = 1000.0
TRADE_RISK_PCT = 0.02  

# --- TRAILING STOP PARAMETERS ---
USE_TRAILING = True
TRAIL_START_R = 1.0   
TRAIL_OFFSET_R = 0.5  

# Initialize Alpaca Client using your config credentials
data_client = CryptoHistoricalDataClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY)

def calculate_heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """Matches the exact lowercase column format returned by Alpaca."""
    ha_df = df.copy()
    ha_df['HA_Close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    
    ha_open = [df['open'].iloc[0]]
    for i in range(1, len(df)):
        ha_open.append((ha_open[i-1] + ha_df['HA_Close'].iloc[i-1]) / 2)
    ha_df['HA_Open'] = ha_open
    
    ha_df['HA_High'] = ha_df[['high', 'HA_Open', 'HA_Close']].max(axis=1)
    ha_df['HA_Low'] = ha_df[['low', 'HA_Open', 'HA_Close']].min(axis=1)
    return ha_df

def run_backtest():
    print(f"📥 Fetching {DAYS_BACK} days of {TIMEFRAME_MINS}m data for {SYMBOL} from Alpaca...")
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=DAYS_BACK)
    
    request_params = CryptoBarsRequest(
        symbol_or_symbols=SYMBOL,
        timeframe=TimeFrame(TIMEFRAME_MINS, TimeFrameUnit.Minute),
        start=start_date,
        end=end_date
    )
    
    try:
        bars = data_client.get_crypto_bars(request_params)
        raw_df = bars.df
        
        if raw_df.empty:
            print("❌ Alpaca returned empty data.")
            return
            
    except Exception as e:
        print(f"❌ Failed to fetch data from Alpaca: {e}")
        return

    # Alpaca returns a MultiIndex (symbol, timestamp). We drop the symbol to easily iterate by time.
    if isinstance(raw_df.index, pd.MultiIndex):
        raw_df = raw_df.reset_index(level=0, drop=True)

    df = calculate_heikin_ashi(raw_df)
    
    bot_state = StrategyState()
    
    capital = INITIAL_CAPITAL
    open_trade = None
    trade_history = []
    
    print("🤖 Simulating Strategy...")

    # WARMUP COUNTER: Skip trading for the first 100 candles to let HA math stabilize
    warmup_candles = 100
    current_candle = 0

    for timestamp, row in df.iterrows():
        current_candle += 1
        
        # Note: Alpaca column names are lowercase ('open', 'high', etc.)
        candle = {
            'open': row['open'], 'high': row['high'], 'low': row['low'], 'close': row['close'],
            'HA_Open': row['HA_Open'], 'HA_Close': row['HA_Close']
        }

        # 1. Manage Open Trade & TRAILING STOP LOGIC
        if open_trade:
            hit_sl = False
            hit_tp = False
            exit_price = 0

            if open_trade['side'] == 'LONG':
                if candle['high'] > open_trade['high_watermark']:
                    open_trade['high_watermark'] = candle['high']
                    
                    if USE_TRAILING and (open_trade['high_watermark'] >= open_trade['entry'] + open_trade['trail_start']):
                        new_sl = open_trade['high_watermark'] - open_trade['trail_offset']
                        if new_sl > open_trade['sl']:
                            open_trade['sl'] = new_sl 

                if candle['low'] <= open_trade['sl']: 
                    hit_sl = True
                    exit_price = open_trade['sl']
                elif candle['high'] >= open_trade['tp']: 
                    hit_tp = True
                    exit_price = open_trade['tp']

            elif open_trade['side'] == 'SHORT':
                if candle['low'] < open_trade['low_watermark']:
                    open_trade['low_watermark'] = candle['low']
                    
                    if USE_TRAILING and (open_trade['low_watermark'] <= open_trade['entry'] - open_trade['trail_start']):
                        new_sl = open_trade['low_watermark'] + open_trade['trail_offset']
                        if new_sl < open_trade['sl']:
                            open_trade['sl'] = new_sl 

                if candle['high'] >= open_trade['sl']: 
                    hit_sl = True
                    exit_price = open_trade['sl']
                elif candle['low'] <= open_trade['tp']: 
                    hit_tp = True
                    exit_price = open_trade['tp']

            if hit_sl or hit_tp:
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
                    'result': 'WIN' if profit > 0 else 'LOSS' 
                })
                open_trade = None 
            continue 

        # 2. Update State
        bot_state.update_state(timestamp, candle)

        # 3. Skip execution during HA warmup
        if current_candle < warmup_candles:
            continue

        # 4. Check Logic
        signal = check_for_signals(bot_state, candle)

        # 5. Execute Entry
        if signal != "NONE":
            real_close = candle['close']
            
            if signal == "LONG":
                risk_amount = real_close - bot_state.ext_low
                sl_price = bot_state.ext_low
                tp_price = real_close + (risk_amount * RR_RATIO)
            else: 
                risk_amount = bot_state.ext_high - real_close
                sl_price = bot_state.ext_high
                tp_price = real_close - (risk_amount * RR_RATIO)

            if risk_amount <= 0: continue
            
            risk_pct = (risk_amount / real_close) * 100
            if risk_pct > MAX_RISK_PCT:
                bot_state.is_outside_down = False
                bot_state.is_outside_up = False
                continue

            qty = (capital * TRADE_RISK_PCT) / risk_amount
            
            open_trade = {
                'side': signal,
                'entry': real_close,
                'sl': sl_price,
                'tp': tp_price,
                'qty': qty,
                'entry_time': timestamp,
                'high_watermark': real_close,
                'low_watermark': real_close,
                'trail_start': risk_amount * TRAIL_START_R,
                'trail_offset': risk_amount * TRAIL_OFFSET_R
            }
            
            bot_state.is_outside_down = False
            bot_state.is_outside_up = False

    # --- PRINT RESULTS ---
    wins = [t for t in trade_history if t['result'] == 'WIN']
    losses = [t for t in trade_history if t['result'] == 'LOSS']
    win_rate = (len(wins) / len(trade_history) * 100) if trade_history else 0
    total_return = ((capital - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100

    print("\n" + "="*40)
    print(f"📊 BACKTEST RESULTS ({DAYS_BACK} Days)")
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