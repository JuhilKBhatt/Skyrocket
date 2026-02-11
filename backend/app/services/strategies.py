# backend/app/services/strategies.py
import pandas as pd
import numpy as np
from typing import List
from app.models.market_data import MarketCandle

def momentum_strategy(df: pd.DataFrame) -> str:
    """RSI-based momentum: Buy > 60, Sell < 40."""
    # Ensure we have enough data
    if len(df) < 15:
        return "HOLD"
        
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    # Avoid division by zero
    rs = gain / loss.replace(0, 0.00001) 
    rsi = 100 - (100 / (1 + rs))
    
    current_rsi = rsi.iloc[-1]
    if pd.isna(current_rsi): return "HOLD"
    
    # Adjusted thresholds slightly to be less restrictive
    if current_rsi > 55: return "BUY"
    if current_rsi < 45: return "SELL"
    return "HOLD"

def ema_trend_strategy(df: pd.DataFrame) -> str:
    """
    EMA Trend Strategy: Replaces Mean Reversion.
    Checks if price is above 50-period EMA (Uptrend) or below (Downtrend).
    """
    if len(df) < 50:
        return "HOLD"

    # Calculate 50-period Exponential Moving Average
    ema_50 = df['close'].ewm(span=50, adjust=False).mean()
    
    current_price = df['close'].iloc[-1]
    current_ema = ema_50.iloc[-1]
    
    if pd.isna(current_ema): return "HOLD"

    if current_price > current_ema: return "BUY"
    if current_price < current_ema: return "SELL"
    return "HOLD"

def volatility_breakout_strategy(df: pd.DataFrame) -> str:
    """Breakout: Buy if price exceeds PREVIOUS 20-day high."""
    if len(df) < 21:
        return "HOLD"

    # FIX: Shift by 1 to compare current price against PAST 20 candles
    # We want the max of the *previous* 20 highs, not including today's developing candle
    high_20 = df['high'].shift(1).rolling(window=20).max()
    low_20 = df['low'].shift(1).rolling(window=20).min()
    
    current_price = df['close'].iloc[-1]
    
    if pd.isna(high_20.iloc[-1]) or pd.isna(low_20.iloc[-1]):
        return "HOLD"

    if current_price >= high_20.iloc[-1]: return "BUY"
    if current_price <= low_20.iloc[-1]: return "SELL"
    return "HOLD"

def get_consensus_signal(candles: List[MarketCandle]) -> str:
    """Coordinates the 3 quant algorithms and returns consensus."""
    if len(candles) < 50: # Increased requirement for EMA calculation
        return "HOLD"

    # Robust DataFrame construction
    data = [{
        'timestamp': c.timestamp,
        'open': c.open,
        'high': c.high,
        'low': c.low,
        'close': c.close,
        'volume': c.volume
    } for c in candles]

    df = pd.DataFrame(data).sort_values('timestamp')
    
    signals = [
        momentum_strategy(df),
        ema_trend_strategy(df),       # Replaced Mean Reversion
        volatility_breakout_strategy(df)
    ]

    # Debug logging to see why it's voting the way it is
    # print(f"Time: {df['timestamp'].iloc[-1]} | Signals: {signals}")

    if signals.count("BUY") >= 2: return "BUY"
    if signals.count("SELL") >= 2: return "SELL"
    return "HOLD"