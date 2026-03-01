# backend/app/services/bot/state_manager.py

class StrategyState:
    def __init__(self):
        self.range_high = None
        self.range_low = None
        self.current_4h_high = None
        self.current_4h_low = None
        
        self.is_outside_up = False
        self.is_outside_down = False
        self.ext_high = None
        self.ext_low = None

    def update_state(self, current_time, latest_candle):
        real_high = latest_candle['high']
        real_low = latest_candle['low']
        ha_close = latest_candle['HA_Close']
        
        # --- PHASE 1: 4-HOUR CYCLE MANAGEMENT ---
        if current_time.hour % 4 == 0 and current_time.minute == 0:
            if self.current_4h_high and self.current_4h_low:
                self.range_high = self.current_4h_high
                self.range_low = self.current_4h_low
            
            self.current_4h_high = real_high
            self.current_4h_low = real_low
            
            self.is_outside_up = False
            self.is_outside_down = False
            self.ext_high = None
            self.ext_low = None
        else:
            self.current_4h_high = max(self.current_4h_high, real_high) if self.current_4h_high else real_high
            self.current_4h_low = min(self.current_4h_low, real_low) if self.current_4h_low else real_low

        # --- PHASE 3: BREAKOUT DETECTION ---
        if self.range_high and self.range_low:
            if ha_close > self.range_high and not self.is_outside_up:
                self.is_outside_up = True
                self.is_outside_down = False
                self.ext_high = real_high
                print("🚨 TRAP ARMED: Broke UP")
                
            if ha_close < self.range_low and not self.is_outside_down:
                self.is_outside_down = True
                self.is_outside_up = False
                self.ext_low = real_low
                print("🚨 TRAP ARMED: Broke DOWN")
                
            # Track Real Extreme Prices
            if self.is_outside_up:
                self.ext_high = max(self.ext_high, real_high)
            if self.is_outside_down:
                self.ext_low = min(self.ext_low, real_low)