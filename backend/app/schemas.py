# backend/app/schemas.py
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

# Watchlist Schemas
class WatchlistBase(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    is_active: bool = True

class WatchlistCreate(WatchlistBase):
    pass

class Watchlist(WatchlistBase):
    id: int
    class Config:
        from_attributes = True

# Global Settings Schemas
class GlobalSettingsBase(BaseModel):
    max_trade_allocation_pct: float
    global_stop_loss_pct: float
    take_profit_pct: float 
    is_trading_enabled: bool

class GlobalSettingsUpdate(GlobalSettingsBase):
    pass

class GlobalSettings(GlobalSettingsBase):
    id: int
    class Config:
        from_attributes = True

class TradeSchema(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    entry_time: datetime
    exit_time: Optional[datetime] = None
    status: str
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None

    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_investment: float
    day_change_pct: float
    yesterday_change_pct: float