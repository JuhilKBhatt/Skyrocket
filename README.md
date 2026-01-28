# Project Skyrocket

---

# 1.0 - Bot Design

## 1.1 - Description

A Voting Based Quant Algorithm Based Trading Bot. Three orthogonal quant strategies, one AI-driven news sentiment model, and one general LLM reasoning layer independently vote on Buy / Sell / Hold decisions

## 1.2 - Tech Stack

### 1.2.1 - Frontend (React+Vite)

* Antdesign Bootstrap
* Configuration only UI (risk limits, toggles, thresholds). No trading logic

### 1.2.2 - Backend (Python)

* Runs Algorithm Models ( Momentum, Mean Reversion, Volatility Breakout )
* Talks to API
* Talk to Frontend

### 1.2.3 - Database (PostgreSQL)

* Algo Models
* Trades Model
* Trade Success/Fail/Loss

### 1.2.4 - API

* Alpaca - Places Trades
* Alpha Vantage - News, Historic & Real Time Data
* Gemini - News & General LLM

## 1.3 - Logic Flow Chart

**1. START: Data Integrity Check**

* **Actions:** Check API Status & Delay, Database Connection, Frontend Connection.
* **IF FAIL:** **→** **( End Operations: Send Email at Error )**
* **IF SUCCESS:** **→** **Proceed to Step 2.**

**2. DECISION: US Market Open Or Closing Hour?**

* **IF NO:** **→** Loop back to **Data Integrity Check** .
* **IF YES:** **→** **Proceed to Step 3** (Pass list of companies & trade details).

**3. PROCESS: Market Scan**

* **Filters:** Liquidity, Volatility, Volume, News & Data API Check.
* **IF NO COMPANIES PASS:** **→** Loop back to **Data Integrity Check** .
* **IF COMPANIES PASS:** **→** **Proceed to Step 4.**

**4. PROCESS: Model Regime Detection**

* **Metrics:** Trend, Range, Volatility.
* **→** **Proceed to Step 5.**

**5. DECISION: Which Regime?**

* **Option A:** **→** **[ High Regime Models ]**
* **Option B:** **→** **[ Normal Models ]**
* **Option C:** **→** **[ Low Regime Models ]**
* *(All 3 paths merge into Step 6)*

**6. PROCESS: Run Quant Algorithm**

* **Inputs:** Quant Algorithm, News & LLM.
* **Logic:**
  * If New Trade Votes: BUY / NO.
  * If Trade Placed: SELL / HOLD.
* **→** **Proceed to Step 7.**

**7. PROCESS: Double Gate Risk Check**

* **Actions:** Add Stop Loss, Time to Live (TTL).
* **Rules:** Max Trade 2% of balance but 5% stop loss.
* **→** **Proceed to Step 8.**

**8. PROCESS: Execute Trade**

* **Action:** Execute via API.
* **→** **Proceed to Step 9.**

**9. PROCESS: Dual Thread Monitoring**

* **Thread A (Fast - Every 1s):** Check Price vs. Stop Loss / Take Profit.

  * *If Stop Hit:* **→** Trigger SELL immediately (Skip to Step 10).
* **Thread B (Slow - Every 1m):** Check Regime Change & Sentiment.

  * *Loop back to Step 4:* Verify if the original thesis (Regime) is still valid.
  * *If Invalid:* **→** Trigger Exit.

**10. PROCESS: Attribution Analysis & Model Refine**

* **Analysis:** Meet Target? Entry/Exit Profit? Model/Vote Success/Fine/Fail? Slippage?
* **→** **Big Loop Back to Step 1 (Data Integrity Check).**

# 2.0 - How to Run

## 2.1 - Setup Environment

## 2.2 - Deployment

### 2.2.1 - Development

### 2.2.2 - Production

### 2.2.3 - Database Management

# 3.0 - Maintenance & Troubleshooting Commands
