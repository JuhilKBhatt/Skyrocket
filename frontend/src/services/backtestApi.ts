// src/services/backtestApi.ts
import { API_URL } from '../config';

export interface BacktestResult {
  ticker: string;
  summary: {
    total_trades: number;
    initial_balance: number;
    final_balance: number;
    total_return_pct: number;
    win_rate: number;
  };
  trades: any[];
  chart_data: { time: string; price: number }[];
}

export const backtestApi = {
  runBacktest: async (ticker: string): Promise<BacktestResult> => {
    const res = await fetch(`${API_URL}/api/backtest/${ticker.toUpperCase()}`);
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Backtest failed');
    }
    return res.json();
  }
};