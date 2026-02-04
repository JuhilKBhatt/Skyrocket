import yfinance as yf
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.market_data import MarketCandle
from app.models.settings import Watchlist

def fetch_and_store_history(ticker: str, db: Session, period: str = "max", interval: str = "1d"):
    """
    Fetches historical data using yfinance and performs a Bulk Upsert.
    """
    print(f"📥 Fetching {ticker} via Yahoo Finance (Period: {period}, Interval: {interval})...")
    
    try:
        # Fetch data
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        
        if df.empty:
            print(f"⚠️ No data found for {ticker}")
            return

        # 1. Build a list of dictionaries (Faster than creating Objects)
        candles_data = []
        for index, row in df.iterrows():
            dt = index.to_pydatetime()
            
            # Strip timezone info to match your DB schema (naive datetime)
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None)

            candles_data.append({
                "symbol": ticker,
                "timestamp": dt,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
                "timeframe": interval
            })

        # 2. Perform Bulk UPSERT (Insert on Conflict Do Update)
        if candles_data:
            stmt = insert(MarketCandle).values(candles_data)
            
            # This logic tells Postgres: "If this symbol+timestamp+timeframe exists, update the prices instead of crashing"
            stmt = stmt.on_conflict_do_update(
                constraint="uq_candle",  # This MUST match the name in your models/market_data.py
                set_={
                    "open": stmt.excluded.open,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "close": stmt.excluded.close,
                    "volume": stmt.excluded.volume,
                }
            )
            
            db.execute(stmt)
            db.commit()
            print(f"✅ Synced {len(candles_data)} candles for {ticker}.")

    except Exception as e:
        print(f"❌ Error fetching {ticker}: {e}")
        db.rollback()

def update_all_watchlists(db: Session):
    """
    Updates all companies. No sleep needed for yfinance!
    """
    active_companies = db.query(Watchlist).filter(Watchlist.is_active == True).all()
    print(f"🔄 Scheduler: Updating {len(active_companies)} companies...")
    
    for company in active_companies:
        # For updates, we fetch the last 5 days of 1-minute data to fill gaps and get live price
        fetch_and_store_history(company.ticker, db, period="5d", interval="1m")