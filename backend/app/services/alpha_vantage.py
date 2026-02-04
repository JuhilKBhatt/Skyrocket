# backend/app/services/alpha_vantage.py
import requests
import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.market_data import MarketCandle
from app.models.settings import Watchlist

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

def fetch_and_store_history(ticker: str, db: Session):
    """
    Fetches full historical daily data for a ticker and stores it in the DB.
    """
    if not ALPHA_VANTAGE_API_KEY:
        print("❌ Error: ALPHA_VANTAGE_API_KEY is missing.")
        return

    print(f"📥 Fetching history for {ticker}...")
    
    # We use TIME_SERIES_DAILY to get historical data
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "full", # 'full' gets up to 20 years of data
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if "Error Message" in data:
            print(f"❌ API Error for {ticker}: {data['Error Message']}")
            return

        time_series = data.get("Time Series (Daily)")
        if not time_series:
            print(f"⚠️ No data found for {ticker}")
            return

        candles_to_add = []
        for date_str, values in time_series.items():
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Create Candle Object
            candle = MarketCandle(
                symbol=ticker,
                timestamp=dt,
                open=float(values["1. open"]),
                high=float(values["2. high"]),
                low=float(values["3. low"]),
                close=float(values["4. close"]),
                volume=int(values["5. volume"]),
                timeframe="1d"
            )
            candles_to_add.append(candle)

        # Batch insert for performance
        # We use 'merge' to avoid duplicates if data overlaps
        for candle in candles_to_add:
            db.merge(candle)
        
        db.commit()
        print(f"✅ Successfully stored {len(candles_to_add)} candles for {ticker}.")

    except Exception as e:
        print(f"❌ Critical Error fetching {ticker}: {e}")
        db.rollback()

def update_all_watchlists(db: Session):
    """
    Loops through all active companies in watchlist and updates them.
    Usage: Call this function periodically (e.g., every 1 hour or market close).
    """
    active_companies = db.query(Watchlist).filter(Watchlist.is_active == True).all()
    print(f"🔄 Updating data for {len(active_companies)} companies...")
    
    for company in active_companies:
        # In a real production app, you might want to use 'outputsize=compact' 
        # for updates to save API credits and bandwidth.
        fetch_and_store_history(company.ticker, db)