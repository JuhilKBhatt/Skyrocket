# backend/app/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

# Watchlist Schemas
class WatchlistBase(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    max_concurrent_trades: int = 1
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
    is_trading_enabled: bool

class GlobalSettingsUpdate(GlobalSettingsBase):
    pass

class GlobalSettings(GlobalSettingsBase):
    id: int
    class Config:
        from_attributes = True