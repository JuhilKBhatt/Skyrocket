# backend/app/models/market_data.py
from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint, BigInteger
from app.core.database import Base

class MarketCandle(Base):
    __tablename__ = "market_candles"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)  # e.g., "AAPL"
    timestamp = Column(DateTime, index=True, nullable=False)
    
    # OHLCV Data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    
    # Optional: Timeframe (e.g., "1m", "5m", "1d")
    timeframe = Column(String, default="1m")

    # Prevent duplicate candles for the same time/symbol
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', 'timeframe', name='uq_candle'),
    )