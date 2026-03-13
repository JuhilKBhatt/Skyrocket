# backend/app/services/bot/execution.py
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from app.core.config import settings
from app.models.trade import Trade, TradeStatus
from datetime import datetime, timezone

trading_client = TradingClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY, paper=True)

def has_open_positions(symbol: str) -> bool:
    try:
        clean_symbol = symbol.replace("/", "")
        positions = trading_client.get_all_positions()
        for pos in positions:
            if pos.symbol == clean_symbol:
                return True
        return False
    except Exception as e:
        print(f"Error checking positions: {e}")
        return True 

def execute_trade(signal: str, current_real_price: float, state, db_settings, symbol: str, db_session):
    print(f"⚡ Executing {signal}...")

    # Extract dynamic risk from UI database
    max_risk_pct = db_settings.global_stop_loss_pct
    rr_ratio = db_settings.take_profit_pct / db_settings.global_stop_loss_pct if db_settings.global_stop_loss_pct > 0 else 2.0
    
    # Calculate Risk Amounts
    if signal == "LONG":
        risk_amount = current_real_price - state.ext_low
        sl_price = state.ext_low
        tp_price = current_real_price + (risk_amount * rr_ratio)
        side = OrderSide.BUY
        db_side = "BUY"
    elif signal == "SHORT":
        risk_amount = state.ext_high - current_real_price
        sl_price = state.ext_high
        tp_price = current_real_price - (risk_amount * rr_ratio)
        side = OrderSide.SELL
        db_side = "SELL"
    else:
        return

    # Max Risk Filter
    if risk_amount <= 0: return
    risk_pct = (risk_amount / current_real_price) * 100
    if risk_pct > max_risk_pct:
        print(f"❌ Cancelled: Stop Loss too wide ({risk_pct:.2f}% > {max_risk_pct}%)")
        return

    # --- DYNAMIC POSITION SIZING ---
    try:
        account = trading_client.get_account()
        buying_power = float(account.equity)
        
        # Max Allocation % (e.g. 50% of account)
        alloc_pct = db_settings.max_trade_allocation_pct / 100.0
        dollars_to_invest = buying_power * alloc_pct
        
        quantity = round(dollars_to_invest / current_real_price, 4)
        
        if quantity <= 0:
            print("❌ Cancelled: Calculated quantity is 0 or negative.")
            return
            
    except Exception as e:
        print(f"❌ Failed to get account balance for sizing: {e}")
        return

    # 1. Submit Market Order ONLY (No Bracket)
    req = MarketOrderRequest(
        symbol=symbol.replace("/", ""),
        qty=quantity,
        side=side,
        time_in_force=TimeInForce.GTC
    )

    try:
        trading_client.submit_order(req)
        print(f"✅ ORDER SUBMITTED: {side.name} {quantity} {symbol} @ ${current_real_price:.2f}")
        print(f"🎯 Target TP: ${tp_price:.2f} | 🛡️ Target SL: ${sl_price:.2f}")
        
        # 2. Log Trade to Database for monitoring
        new_trade = Trade(
            symbol=symbol,
            side=db_side,
            quantity=quantity,
            entry_price=current_real_price,
            status=TradeStatus.OPEN,
            strategy="HAFakeoutScalper"
            # We will use 'pnl' and 'pnl_percent' columns to temporarily store our target SL/TP values 
            # while the trade is open so the runner can monitor them. 
            # (A cleaner approach would be adding dedicated sl_target/tp_target columns to the Trade model)
        )
        # Using PNL field to store TP and PNL_PERCENT to store SL targets temporarily
        new_trade.pnl = tp_price 
        new_trade.pnl_percent = sl_price

        db_session.add(new_trade)
        db_session.commit()

        # Reset Trap
        state.is_outside_down = False
        state.is_outside_up = False

    except Exception as e:
        print(f"❌ Alpaca Order Error: {e}")