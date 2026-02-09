// src/services/tradesApi.ts
import { API_URL } from '../config';

export interface TradeType {
    id: number;
    symbol: string;
    side: string;
    quantity: number;
    entry_price: number;
    exit_price?: number;
    exit_time?: string;
    pnl?: number;
    pnl_percent?: number;
    status: string;
}

export const tradesApi = {
    getActiveTrades: async (): Promise<TradeType[]> => {
        const res = await fetch(`${API_URL}/api/trades/active`);
        return res.json();
    },
    getHistory: async (): Promise<TradeType[]> => {
        const res = await fetch(`${API_URL}/api/trades/history`);
        return res.json();
    },
    getStats: async () => {
        const res = await fetch(`${API_URL}/api/trades/stats`);
        return res.json();
    }
};