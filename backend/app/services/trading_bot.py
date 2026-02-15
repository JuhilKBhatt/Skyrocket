# backend/app/services/trading_bot.py
from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from datetime import datetime 
from timedelta import Timedelta 
from finbert_utils import estimate_sentiment
import os
import requests
import json
import gc # Garbage Collection (Critical for memory)
import torch # To clear AI memory

# --- CONFIGURATION ---
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_BASE_URL")

ALPACA_CREDS = {
    "API_KEY":API_KEY, 
    "API_SECRET": API_SECRET, 
    "PAPER": True
}

class MLTrader(Strategy): 
    def initialize(self, symbol:str="SPY", cash_at_risk:float=.5): 
        self.symbol = symbol
        self.sleeptime = "24H" 
        self.last_trade = None 
        self.cash_at_risk = cash_at_risk
        
    def position_sizing(self): 
        cash = self.get_cash() 
        last_price = self.get_last_price(self.symbol)
        
        if last_price is None:
            return cash, None, 0

        quantity = round(cash * self.cash_at_risk / last_price,0)
        return cash, last_price, quantity

    def get_dates(self): 
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def cleanup_memory(self):
        """Forces the system to release memory to prevent 'Killed' errors"""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def get_sentiment(self): 
        today, three_days_prior = self.get_dates()
        today_str = today.strftime('%Y-%m-%d')
        
        # --- DISK-BASED CACHE LOGIC ---
        cache_file = "news_cache.json"
        
        # Load cache from disk just for this check (keeps RAM low)
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                try:
                    file_cache = json.load(f)
                except:
                    file_cache = {}
        else:
            file_cache = {}

        if today_str in file_cache:
            return file_cache[today_str][0], file_cache[today_str][1]
        # -------------------------------

        # If not in cache, fetch from API
        url = "https://data.alpaca.markets/v1beta1/news"
        headers = {
            "APCA-API-KEY-ID": API_KEY,
            "APCA-API-SECRET-KEY": API_SECRET
        }
        params = {
            "symbols": self.symbol,
            "start": three_days_prior,
            "end": today,
            "limit": 50,  # Fetch 50 headlines
            "sort": "desc"
        }
        
        final_news = []
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                all_headlines = [ev["headline"] for ev in data.get("news", [])]
                
                # Filter logic
                final_news = [h for h in all_headlines if self.symbol in h or self.symbol.lower() in h.lower()]
                if not final_news:
                    final_news = all_headlines[:5]
                else:
                    final_news = final_news[:5]

        except Exception as e:
            print(f"⚠️ News Error: {e}")

        # Run AI
        probability, sentiment = estimate_sentiment(final_news)
        
        # --- SAVE TO DISK IMMEDIATELY ---
        file_cache[today_str] = [probability, sentiment]
        with open(cache_file, "w") as f:
            json.dump(file_cache, f)
        # --------------------------------
        
        return probability, sentiment

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing() 
        
        if last_price is None:
            return

        probability, sentiment = self.get_sentiment()

        print(f"📊 {self.symbol} Sentiment: {sentiment} ({probability:.2f})")

        if cash > last_price: 
            # Changed threshold from .999 to .85 so it actually trades
            if sentiment == "positive" and probability > .85: 
                if self.last_trade == "sell": 
                    self.sell_all() 
                
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "buy", 
                    type="bracket", 
                    take_profit_price=last_price*1.20, 
                    stop_loss_price=last_price*.95
                )
                self.submit_order(order) 
                self.last_trade = "buy"
                
            elif sentiment == "negative" and probability > .85: 
                if self.last_trade == "buy": 
                    self.sell_all() 
                
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "sell", 
                    type="bracket", 
                    take_profit_price=last_price*.8, 
                    stop_loss_price=last_price*1.05
                )
                self.submit_order(order) 
                self.last_trade = "sell"
        
        # CRITICAL: Clean memory to prevent crashing
        self.cleanup_memory()

# --- RUNNER ---
if __name__ == "__main__":
    start_date = datetime(2024,1,1)
    end_date = datetime(2024,12,31) 
    
    # You can change "SPY" to "AAPL" or "NVDA" here
    symbol = "SPY" 

    broker = Alpaca(ALPACA_CREDS) 
    strategy = MLTrader(name='mlstrat', broker=broker, 
                        parameters={"symbol": symbol, 
                                    "cash_at_risk":.5})
    
    strategy.backtest(
        YahooDataBacktesting, 
        start_date, 
        end_date, 
        parameters={"symbol": symbol, "cash_at_risk":.5}
    )