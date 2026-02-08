# backend/app/services/market_data.py
import os
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.market_data import MarketCandle
from app.models.settings import Watchlist
from alpaca.data import StockHistoricalDataClient, TimeFrame, TimeFrameUnit, StockBarsRequest

# Load keys from environment
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

THIRTY_MIN = TimeFrame(30, TimeFrameUnit.Minute)

client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

def fetch_and_store_history(ticker: str, db: Session, timeframe=THIRTY_MIN, days_back=1825):
    print(f"📥 Fetching {ticker} via Alpaca ({timeframe.value})...")
    
    start_time = datetime.now() - timedelta(days=days_back)
    
    request_params = StockBarsRequest(
        symbol_or_symbols=ticker,
        timeframe=timeframe,
        start=start_time
    )

    try:
        bars_obj = client.get_stock_bars(request_params)
        if not bars_obj or bars_obj.df.empty:
            return

        bars = bars_obj.df
        candles_data = []
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
    """Regular update loop used by the scheduler."""
    active_companies = db.query(Watchlist).filter(Watchlist.is_active == True).all()
    for company in active_companies:
        # Fetch last 1 day of 30-minute data to ensure continuity
        fetch_and_store_history(company.ticker, db, timeframe=THIRTY_MIN, days_back=1)

def backfill_missing_candles(db: Session):
    """Runs on startup to fill gaps caused by downtime."""
    print("🔍 Checking for data gaps since last shutdown...")
    active_companies = db.query(Watchlist).filter(Watchlist.is_active == True).all()
    
    for company in active_companies:
        last_candle_ts = db.query(func.max(MarketCandle.timestamp)).filter(
            MarketCandle.symbol == company.ticker,
            MarketCandle.timeframe == THIRTY_MIN.value
        ).scalar()

        if last_candle_ts:
            last_candle_ts = last_candle_ts.replace(tzinfo=None)
            delta = datetime.now() - last_candle_ts
            
            # If gap is > 30 mins, fetch enough history to cover it
            if delta.total_seconds() > 1800:
                days_to_fetch = delta.days + 1
                print(f"⏳ Backfilling {company.ticker} ({days_to_fetch} days needed)...")
                fetch_and_store_history(company.ticker, db, timeframe=THIRTY_MIN, days_back=days_to_fetch)
            else:
                print(f"✅ {company.ticker} is up-to-date.")
        else:
            print(f"🆕 No data for {company.ticker}. Performing initial 5-year sync...")
            fetch_and_store_history(company.ticker, db, timeframe=THIRTY_MIN, days_back=1825)