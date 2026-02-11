# backend/app/services/strategies.py
import pandas as pd
from typing import List
from app.models.market_data import MarketCandle

def get_combined_signal(candles: List[MarketCandle]) -> str:
    """
    Coordinates three quantitative signals.
    Returns: 'BUY', 'SELL', or 'HOLD'.
    """
    if len(candles) < 20:
        return "HOLD"

    df = pd.DataFrame([c.__dict__ for c in candles])
    close = df['close']

    # 1. Momentum Signal (RSI-style logic)
    rsi_signal = "BUY" if close.iloc[0] > close.iloc[1] else "HOLD"

    # 2. Trend Signal (Moving Average crossover)
    sma_20 = close.mean()
    trend_signal = "BUY" if close.iloc[0] > sma_20 else "SELL"

    # 3. Volatility Signal (Simplified Bollinger Band)
    std_dev = close.std()
    vol_signal = "HOLD" if std_dev > 1.0 else "BUY"

    # Consensus Logic
    signals = [rsi_signal, trend_signal, vol_signal]
    if signals.count("BUY") >= 2: return "BUY"
    if signals.count("SELL") >= 2: return "SELL"
    return "HOLD"