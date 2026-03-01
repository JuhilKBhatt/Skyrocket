# Project Skyrocket

---

# 1.0 - Bot Design - Depreciated

## 1.1 - Description

Trading Bot designed on 15m candle for bitcoin:USD

## 1.2 - Tech Stack

### 1.2.1 - Frontend (React+Vite)

* Antdesign Bootstrap
* Configuration only UI (risk limits, toggles, thresholds). No trading logic

### 1.2.2 - Backend (Python)

* Calculates Trade ( Momentum, Mean Reversion, Volatility Breakout )
* Talks to API
* Talk to Frontend - Settings Only

### 1.2.3 - Database (PostgreSQL)

* Market Data

### 1.2.4 - API

* Alpaca - Places Trades

## 1.3 - Logic Flow Chart

🔄 The Main Loop (Runs every 15 minutes on candle close)
1️⃣ Phase 1: 4-Hour Cycle Management

Check Time: Is it a new 4-Hour boundary? (e.g., 00:00, 04:00, 08:00, 12:00 UTC)

IF YES:

Range_High = Highest price of the previous 4 hours.

Range_Low = Lowest price of the previous 4 hours.

Reset Variables: isOutsideUp = False, isOutsideDown = False, ExtremeHigh = None, ExtremeLow = None.

IF NO:

Keep tracking the highest/lowest prices of the current 4H period in the background (to be used when the next 4H boundary hits).

2️⃣ Phase 2: Position Check

Check Alpaca: Do we currently have an open trade?

IF YES: Do nothing. Let Alpaca handle the Take Profit, Stop Loss, or Trailing Stop. (End loop).

IF NO: Proceed to Phase 3.

3️⃣ Phase 3: Breakout Detection (Arming the Trap)

Check Upper Breakout:

Did the Heikin Ashi (HA) Close just close ABOVE Range_High?

IF YES: Set isOutsideUp = True and set isOutsideDown = False.

Check Lower Breakout:

Did the Heikin Ashi (HA) Close just close BELOW Range_Low?

IF YES: Set isOutsideDown = True and set isOutsideUp = False.

Track Extremes (Crucial for Stop Loss):

If isOutsideUp == True: Keep tracking the absolute highest real price reached (ExtremeHigh).

If isOutsideDown == True: Keep tracking the absolute lowest real price reached (ExtremeLow).

4️⃣ Phase 4: Re-Entry & Momentum Check (Springing the Trap)

Check LONG Conditions:

Was the trap armed? (isOutsideDown == True)

Did price snap back inside? (HA Close > Range_Low)

Is momentum bullish? (HA Close > HA Open / Green HA Candle)

If all 3 are YES ➡️ Proceed to Phase 5 for a LONG.

Check SHORT Conditions:

Was the trap armed? (isOutsideUp == True)

Did price snap back inside? (HA Close < Range_High)

Is momentum bearish? (HA Close < HA Open / Red HA Candle)

If all 3 are YES ➡️ Proceed to Phase 5 for a SHORT.

5️⃣ Phase 5: Risk Calculation & Execution

Calculate Risk:

Long: Risk = Current Real Close - ExtremeLow

Short: Risk = ExtremeHigh - Current Real Close

Risk % Filter Check:

Risk % = (Risk / Current Real Close) * 100

Is Risk % > Max Risk % (e.g., 0.5%)?

IF YES: The breakout went too far, the Stop Loss is too wide. CANCEL TRADE. Reset trap variables to False.

IF NO: Proceed to Execution.

Send Bracket Order to Alpaca:

Calculate Stop Loss (SL): ExtremeLow (Long) or ExtremeHigh (Short).

Calculate Take Profit (TP): Entry Price ± (Risk * Reward Ratio).

Submit a Bracket Order to Alpaca with the SL and TP. (Note: You will also program Alpaca's Trailing Stop parameters here).

Reset trap variables to False (isOutsideUp/Down = False).

# 2.0 - How to Run

## 2.1 - Setup Environment

### 2.1.1 - Create .env file at root (For Prod)

```
# .env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
ALPHA_VANTAGE_API_KEY=""
ALPACA_API_KEY=""
ALPACA_SECRET_KEY=""
ALPACA_BASE_URL=""
HF_TOKEN=""
```

## 2.2 - Deployment

### 2.2.1 - Development

Run:

```
docker-compose -f docker-compose.dev.yml down

docker-compose -f docker-compose.dev.yml up --build -d
```

Access:

* Frontend: `http://localhost:5173`
* Backend API Docs: `http://localhost:8000/docs`
* Database: `localhost:5432`

### 2.2.2 - Production

Run:

```
docker-compose -f docker-compose.prod.yml down

docker-compose -f docker-compose.prod.yml up --build -d
```

Access:

* Application: `http://localhost:759758`

### 2.2.3 - Database Management

# 3.0 - Maintenance & Troubleshooting Commands

python3 manage_db.py update -m "Added settings tables"

docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

## 3.1 - Database

**1. Development (Default)** Running without arguments targets **`skyrocket_dev` using** `docker-compose.dev.yml`.

* **View Data:** `python3 manage_db.py view`
* **Update Models:** `python3 manage_db.py update -m "Added trade column"`
* **Reset DB:** `python3 manage_db.py delete`

**2. Production** Add the **`--env prod` flag to target** **`skyrocket_prod` using** `docker-compose.prod.yml`.

* **View Data:** `python3 manage_db.py --env prod view`
* **Restore Backup:** `python3 manage_db.py --env prod restore backup_v1.sql`
* **Wipe Data:** `python3 manage_db.py --env prod delete` *(Will ask for "DESTROY" confirmation)*
