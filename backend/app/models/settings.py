# backend/app/models/settings.py
from sqlalchemy import Column, Integer, String, Float, Boolean
from app.core.database import Base

class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String)
    max_concurrent_trades = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

class GlobalSettings(Base):
    __tablename__ = "global_settings"

    id = Column(Integer, primary_key=True)
    # Singleton row pattern or Key-Value pair
    max_trade_allocation_pct = Column(Float, default=2.0)
    global_stop_loss_pct = Column(Float, default=5.0)
    is_trading_enabled = Column(Boolean, default=False)