# backend/app/routers/backtest.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.backtester import run_backtest

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

@router.get("/{ticker}")
def execute_backtest(ticker: str, db: Session = Depends(get_db)):
    result = run_backtest(db, ticker.upper())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result