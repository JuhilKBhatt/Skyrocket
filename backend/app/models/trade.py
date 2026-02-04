# backend/app/models/trade.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class TradeStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PENDING = "PENDING"

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    
    # Trade Details
    side = Column(String, nullable=False) # "BUY" or "SELL"
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True) # Null until closed
    
    # Timestamps
    entry_time = Column(DateTime(timezone=True), server_default=func.now())
    exit_time = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    status = Column(Enum(TradeStatus), default=TradeStatus.OPEN)
    strategy = Column(String, nullable=True) # e.g., "Momentum_V1"
    pnl = Column(Float, nullable=True) # Profit/Loss amount
    pnl_percent = Column(Float, nullable=True)