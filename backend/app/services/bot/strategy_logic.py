# backend/app/services/bot/strategy_logic.py

def check_for_signals(state, latest_candle) -> str:
    if not state.range_high or not state.range_low:
        return "NONE"

    ha_close = latest_candle['HA_Close']
    ha_open = latest_candle['HA_Open']
    
    is_ha_green = ha_close > ha_open
    is_ha_red = ha_close < ha_open

    if state.is_outside_down and ha_close > state.range_low and is_ha_green:
        return "LONG"
        
    if state.is_outside_up and ha_close < state.range_high and is_ha_red:
        return "SHORT"

    return "NONE"