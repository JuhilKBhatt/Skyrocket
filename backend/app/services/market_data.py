# backend/app/services/market_data.py
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.market_data import MarketCandle
from app.models.settings import Watchlist

# Map our internal string representation to Pandas resample rules
TIMEFRAMES = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1D"
}

# yfinance lookback limits per interval
YF_MAX_PERIODS = {
    "1m": "7d",
    "5m": "60d",
    "15m": "60d",
    "30m": "60d",
    "1h": "730d",
    "4h": "730d",
    "1d": "max"
}

def _upsert_candles(db: Session, candles_data: list, ticker: str, timeframe: str):
    """Helper method to handle the database upsert logic."""
    if not candles_data:
        return

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
    print(f"✅ Upserted {len(candles_data)} {timeframe} bars for {ticker}.")


def df_to_dict_list(df: pd.DataFrame, ticker: str, timeframe_str: str) -> list:
    """Converts a Pandas DataFrame to a list of dicts for SQLAlchemy."""
    candles = []
    for timestamp, row in df.iterrows():
        # Drop rows with NaN values that can occur during market closed hours in resampling
        if pd.isna(row["Open"]):
            continue
            
        candles.append({
            "symbol": ticker,
            "timestamp": timestamp.to_pydatetime().replace(tzinfo=None),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]),
            "timeframe": timeframe_str
        })
    return candles


def resample_and_store(df_1m: pd.DataFrame, ticker: str, db: Session):
    """Takes 1m DataFrame, resamples to higher timeframes, and stores them."""
    if df_1m.empty:
        return

    # Pandas aggregation dictionary for OHLCV data
    agg_dict = {
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    }

    # Iterate through all higher timeframes and resample
    for tf_label, pandas_rule in TIMEFRAMES.items():
        if tf_label == "1m":
            continue # Already handled
            
        print(f"🔄 Resampling {ticker} 1m data into {tf_label}...")
        
        # Resample the data
        resampled_df = df_1m.resample(pandas_rule).agg(agg_dict)
        resampled_df.dropna(inplace=True) # Clean up empty periods (after hours, weekends)
        
        # Convert and store
        candles_data = df_to_dict_list(resampled_df, ticker, tf_label)
        _upsert_candles(db, candles_data, ticker, tf_label)


def initial_seed_history(ticker: str, db: Session):
    """Fetches max available history for all timeframes directly from yfinance."""
    print(f"🆕 Initializing deep history for {ticker}...")
    yf_ticker = yf.Ticker(ticker)

    for tf_label in TIMEFRAMES.keys():
        period = YF_MAX_PERIODS[tf_label]
        print(f"📥 Seeding {ticker} {tf_label} (Period: {period})...")
        try:
            # yfinance expects interval in lowercase like '1m', '1d' etc. (matches our keys)
            df = yf_ticker.history(period=period, interval=tf_label)
            if not df.empty:
                candles = df_to_dict_list(df, ticker, tf_label)
                _upsert_candles(db, candles, ticker, tf_label)
        except Exception as e:
            print(f"❌ Error seeding {tf_label} for {ticker}: {e}")
            db.rollback()


def maintain_market_data(ticker: str, db: Session, period: str = "1d"):
    """Regular maintenance: Fetches 1m data and propagates it upwards."""
    print(f"📥 Fetching latest 1m data for {ticker} (Period: {period})...")
    try:
        yf_ticker = yf.Ticker(ticker)
        df_1m = yf_ticker.history(period=period, interval="1m")
        
        if df_1m.empty:
            print(f"⚠️ No new 1m data found for {ticker}.")
            return

        # 1. Store the 1m base data
        candles_1m = df_to_dict_list(df_1m, ticker, "1m")
        _upsert_candles(db, candles_1m, ticker, "1m")

        # 2. Resample and store all higher timeframes using the 1m data
        resample_and_store(df_1m, ticker, db)

    except Exception as e:
        print(f"❌ Maintenance error for {ticker}: {e}")
        db.rollback()


def update_all_watchlists(db: Session):
    """Regular update loop used by the scheduler (runs every few minutes)."""
    active_companies = db.query(Watchlist).filter(Watchlist.is_active == True).all()
    for company in active_companies:
        # Fetch the last 1 day of 1m data and resample upward
        maintain_market_data(company.ticker, db, period="1d")


def backfill_missing_candles(db: Session):
    """Runs on startup to catch up on data missed during downtime."""
    print("🔍 Checking for data gaps since last shutdown...")
    active_companies = db.query(Watchlist).filter(Watchlist.is_active == True).all()
    
    for company in active_companies:
        # We only check the 1m timeframe. Because we resample, 
        # if 1m is up to date, the higher timeframes will be too.
        last_1m_ts = db.query(func.max(MarketCandle.timestamp)).filter(
            MarketCandle.symbol == company.ticker,
            MarketCandle.timeframe == "1m"
        ).scalar()

        if not last_1m_ts:
            # No data exists at all. Do a full historical seed.
            initial_seed_history(company.ticker, db)
            continue

        last_1m_ts = last_1m_ts.replace(tzinfo=None)
        delta = datetime.now() - last_1m_ts
        minutes_offline = delta.total_seconds() / 60

        if minutes_offline > 1:
            days_offline = delta.days + 1
            
            # Clamp the backfill to yfinance's 7-day 1m limit
            if days_offline > 7:
                print(f"⚠️ {company.ticker} was offline for {days_offline} days. Capping 1m backfill to 7 days due to yfinance limits.")
                days_offline = 7
                
            print(f"⏳ Backfilling {company.ticker} via 1m resample ({days_offline} days needed)...")
            maintain_market_data(company.ticker, db, period=f"{days_offline}d")
        else:
            print(f"✅ {company.ticker} is completely up-to-date.")