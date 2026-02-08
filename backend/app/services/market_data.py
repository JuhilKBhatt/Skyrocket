# app/services/market_data.py
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.market_data import MarketCandle
from app.models.settings import Watchlist
from alpaca.data import StockHistoricalDataClient, TimeFrame, StockBarsRequest

# Load keys from environment
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
THIRTY_MIN = TimeFrame(30, TimeFrame.Minute)

client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

def fetch_and_store_history(ticker: str, db: Session, timeframe=THIRTY_MIN, days_back=1825):
    """
    Fetches historical bars from Alpaca and syncs to DB using UPSERT.
    """
    print(f"📥 Fetching {ticker} via Alpaca ({timeframe.value})...")
    
    start_time = datetime.now() - timedelta(days=days_back)
    
    request_params = StockBarsRequest(
        symbol_or_symbols=ticker,
        timeframe=timeframe,
        start=start_time
    )

    try:
        # Fetch bars and convert to DataFrame
        bars = client.get_stock_bars(request_params).df
        if bars.empty:
            return

        candles_data = []
        # Alpaca multi-index DF has (symbol, timestamp)
        for (symbol, timestamp), row in bars.iterrows():
            candles_data.append({
                "symbol": symbol,
                "timestamp": timestamp.to_pydatetime().replace(tzinfo=None),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
                "timeframe": timeframe.value
            })

        if candles_data:
            stmt = insert(MarketCandle).values(candles_data)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_candle",
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
            print(f"✅ Synced {len(candles_data)} Alpaca bars for {ticker}.")

    except Exception as e:
        print(f"❌ Alpaca Error for {ticker}: {e}")
        db.rollback()

def update_all_watchlists(db: Session):
    active_companies = db.query(Watchlist).filter(Watchlist.is_active == True).all()
    for company in active_companies:
        # Fetch last 1 day of 1-minute data for the update loop
        fetch_and_store_history(company.ticker, db, timeframe=THIRTY_MIN, days_back=1)