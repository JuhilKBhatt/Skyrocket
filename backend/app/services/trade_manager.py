# backend/app/services/trade_manager.py
import os
from sqlalchemy.orm import Session
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from app.models.settings import Watchlist, GlobalSettings
from app.models.trade import Trade, TradeStatus
from app.services.algorithm_manager import get_trade_decision

# Initialize Alpaca Trading Client (Paper Trading by default)
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

def run_trade_cycle(db: Session):
    """Main loop for executing trades via Alpaca."""
    settings = db.query(GlobalSettings).first()
    if not settings or not settings.is_trading_enabled:
        return

    watchlist = db.query(Watchlist).filter(Watchlist.is_active == True).all()

    for item in watchlist:
        decision = get_trade_decision(db, item.ticker)
        
        # Check if we already have an open trade in our DB
        open_trade = db.query(Trade).filter(
            Trade.symbol == item.ticker, 
            Trade.status == TradeStatus.OPEN
        ).first()

        if decision == "BUY" and not open_trade:
            execute_alpaca_buy(db, item, settings)
        
        elif decision == "SELL" and open_trade:
            execute_alpaca_sell(db, open_trade)

def execute_alpaca_buy(db: Session, item: Watchlist, settings: GlobalSettings):
    """Executes a Market Buy on Alpaca and logs to DB."""
    try:
        # Simplified quantity logic based on allocation %
        # In production, check trading_client.get_account().cash first
        qty = 1 
        
        order_details = MarketOrderRequest(
            symbol=item.ticker,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC
        )
        
        # SEND TO ALPACA
        order = trading_client.submit_order(order_data=order_details)
        
        # LOG TO LOCAL DB
        new_trade = Trade(
            symbol=item.ticker,
            side="BUY",
            quantity=qty,
            entry_price=float(order.filled_avg_price or 0), 
            status=TradeStatus.OPEN
        )
        db.add(new_trade)
        db.commit()
        print(f"🚀 Alpaca Buy Order Executed: {item.ticker}")
    except Exception as e:
        print(f"❌ Alpaca Buy Error: {e}")

def execute_alpaca_sell(db: Session, trade: Trade):
    """Executes a Market Sell on Alpaca and closes DB record."""
    try:
        order_details = MarketOrderRequest(
            symbol=trade.symbol,
            qty=trade.quantity,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC
        )
        
        trading_client.submit_order(order_data=order_details)
        
        # Update local DB trade record
        trade.status = TradeStatus.CLOSED
        db.commit()
        print(f"🏁 Alpaca Sell Order Executed: {trade.symbol}")
    except Exception as e:
        print(f"❌ Alpaca Sell Error: {e}")