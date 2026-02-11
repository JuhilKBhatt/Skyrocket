# backend/app/services/strategies.py
import pandas as pd
from typing import List
from app.models.market_data import MarketCandle

def get_combined_signal(candles: List[MarketCandle]) -> str:
    if len(candles) < 20:
        return "HOLD"

    # Convert to DataFrame for easier calculation
    df = pd.DataFrame([c.__dict__ for c in candles])
    close = df['close']

    # 1. Momentum Signal (Simple RSI-like logic)
    # Buy if price is increasing, Sell if decreasing
    if close.iloc[0] > close.iloc[1] * 1.005:
        rsi_signal = "BUY"
    elif close.iloc[0] < close.iloc[1] * 0.995:
        rsi_signal = "SELL"
    else:
        rsi_signal = "HOLD"

    # 2. Trend Signal (Moving Average crossover)
    sma_20 = close.head(20).mean()
    trend_signal = "BUY" if close.iloc[0] > sma_20 else "SELL"

    # 3. Volatility Signal (Exit if volatility spikes too high)
    std_dev = close.head(10).std()
    if std_dev < 0.5:
        vol_signal = "BUY"
    elif std_dev > 2.0:
        vol_signal = "SELL"
    else:
        vol_signal = "HOLD"

    # Consensus Logic
    signals = [rsi_signal, trend_signal, vol_signal]
    
    # Require at least 2 components to agree
    if signals.count("BUY") >= 2: 
        return "BUY"
    if signals.count("SELL") >= 2: 
        return "SELL"
    
    return "HOLD"