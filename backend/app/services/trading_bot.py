# backend/app/services/trading_bot.py
from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from datetime import datetime 
from timedelta import Timedelta 
from finbert_utils import estimate_sentiment
import os
import sys
import requests
import json
import gc 
import torch 

# Add the parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.models.sentiment import NewsSentiment

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
    # 1. Added tp_pct and sl_pct to initialize arguments
    def initialize(self, symbol:str="SPY", cash_at_risk:float=.5, tp_pct:float=.10, sl_pct:float=.05): 
        self.symbol = symbol
        self.sleeptime = "24H" 
        self.last_trade = None 
        self.cash_at_risk = cash_at_risk
        self.tp_pct = tp_pct  # Store Take Profit %
        self.sl_pct = sl_pct  # Store Stop Loss %
        
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
        return today, three_days_prior

    def cleanup_memory(self):
        """Forces the system to release memory to prevent 'Killed' errors"""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def get_sentiment(self): 
        today, three_days_prior = self.get_dates()
        today_str = today.strftime('%Y-%m-%d')
        cache_key = f"{self.symbol}_{today_str}"
        
        # --- DATABASE CHECK ---
        db = SessionLocal()
        try:
            db_sentiment = db.query(NewsSentiment).filter(
                NewsSentiment.symbol == self.symbol,
                NewsSentiment.date == today.date() 
            ).first()
            
            if db_sentiment:
                print(f"DYCA Found in DB: {self.symbol} on {today_str}")
                return db_sentiment.sentiment_score, db_sentiment.sentiment_label
        except Exception as e:
            print(f"⚠️ DB Read Error: {e}")
        finally:
            db.close()

        # --- DISK-BASED JSON CACHE (Fallback) ---
        cache_file = "news_cache.json"
        file_cache = {}
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    file_cache = json.load(f)
            except:
                file_cache = {}

        if cache_key in file_cache:
            return file_cache[cache_key][0], file_cache[cache_key][1]

        # If not in DB or JSON, fetch from API
        print(f"qv Fetching new data for {self.symbol}...")
        url = "https://data.alpaca.markets/v1beta1/news"
        headers = {
            "APCA-API-KEY-ID": API_KEY,
            "APCA-API-SECRET-KEY": API_SECRET
        }
        params = {
            "symbols": self.symbol,
            "start": three_days_prior.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "end": today.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "limit": 50,
            "sort": "desc"
        }
        
        final_news = []
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                all_headlines = [ev["headline"] for ev in data.get("news", [])]
                
                final_news = [h for h in all_headlines if self.symbol in h or self.symbol.lower() in h.lower()]
                if not final_news:
                    final_news = all_headlines[:5]
                else:
                    final_news = final_news[:5]
        except Exception as e:
            print(f"⚠️ News Error: {e}")

        probability, sentiment = estimate_sentiment(final_news)
        
        # --- SAVE TO DATABASE ---
        db = SessionLocal()
        try:
            new_entry = NewsSentiment(
                symbol=self.symbol,
                date=today.date(),
                sentiment_score=probability,
                sentiment_label=sentiment
            )
            db.add(new_entry)
            db.commit()
            print(f"💾 Saved to DB: {self.symbol}")
        except Exception as e:
            print(f"⚠️ DB Save Error: {e}")
            db.rollback()
        finally:
            db.close()

        # --- SAVE TO JSON CACHE ---
        file_cache[cache_key] = [probability, sentiment]
        with open(cache_file, "w") as f:
            json.dump(file_cache, f)
        
        return probability, sentiment

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing() 
        
        if last_price is None:
            return

        probability, sentiment = self.get_sentiment()

        print(f"📊 {self.symbol} Sentiment: {sentiment} ({probability:.2f})")

        if cash > last_price: 
            if sentiment == "positive" and probability > .85: 
                if self.last_trade == "sell": 
                    self.sell_all() 
                
                # 2. Use self.tp_pct and self.sl_pct for Buy Order
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "buy", 
                    type="bracket", 
                    take_profit_price=last_price * (1 + self.tp_pct), 
                    stop_loss_price=last_price * (1 - self.sl_pct)
                )
                self.submit_order(order) 
                self.last_trade = "buy"
                
            elif sentiment == "negative" and probability > .85: 
                if self.last_trade == "buy": 
                    self.sell_all() 
                
                # 3. Use self.tp_pct and self.sl_pct for Short Order
                # Note: For shorts, TP is lower than entry, SL is higher
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "sell", 
                    type="bracket", 
                    take_profit_price=last_price * (1 - self.tp_pct), 
                    stop_loss_price=last_price * (1 + self.sl_pct)
                )
                self.submit_order(order) 
                self.last_trade = "sell"
        
        self.cleanup_memory()

# --- RUNNER ---
if __name__ == "__main__":
    start_date = datetime(2024,1,1)
    end_date = datetime(2025,12,31) 
    
    # 4. SETTINGS - Change these to adjust strategy behavior
    symbol = "SPY" 
    cash_at_risk = 0.5  # 5% of available cash per trade
    take_profit = 0.10  # 10% gain
    stop_loss = 0.06    # 4% loss

    broker = Alpaca(ALPACA_CREDS) 
    
    # 5. Pass parameters dictionary to MLTrader
    strategy = MLTrader(
        name='mlstrat', 
        broker=broker, 
        parameters={
            "symbol": symbol, 
            "cash_at_risk": cash_at_risk,
            "tp_pct": take_profit,
            "sl_pct": stop_loss
        }
    )
    
    strategy.backtest(
        YahooDataBacktesting, 
        start_date, 
        end_date, 
        parameters={
            "symbol": symbol, 
            "cash_at_risk": cash_at_risk,
            "tp_pct": take_profit,
            "sl_pct": stop_loss
        }
    )