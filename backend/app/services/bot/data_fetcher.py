# backend/app/services/bot/data_fetcher.py
import pandas as pd
from datetime import datetime, timedelta, timezone
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from app.core.config import settings

# Initialize Alpaca Data Client
data_client = CryptoHistoricalDataClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY)

def calculate_heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    ha_df = df.copy()
    ha_df['HA_Close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    
    ha_open = [df['open'].iloc[0]]
    for i in range(1, len(df)):
        ha_open.append((ha_open[i-1] + ha_df['HA_Close'].iloc[i-1]) / 2)
    ha_df['HA_Open'] = ha_open
    
    ha_df['HA_High'] = ha_df[['high', 'HA_Open', 'HA_Close']].max(axis=1)
    ha_df['HA_Low'] = ha_df[['low', 'HA_Open', 'HA_Close']].min(axis=1)
    
    return ha_df

def get_latest_data(symbol: str) -> pd.DataFrame:
    request_params = CryptoBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame(15, TimeFrameUnit.Minute),
        start=datetime.now(timezone.utc) - timedelta(days=4) 
    )
    
    bars = data_client.get_crypto_bars(request_params)
    if not bars or bars.df.empty:
        return pd.DataFrame()
    
    df = bars.df
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index(level=0, drop=True)
        
    return calculate_heikin_ashi(df)