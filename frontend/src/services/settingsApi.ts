import { API_URL } from '../config';

export interface CompanyDataType {
  id?: number;
  ticker: string;
  company_name: string;
  is_active?: boolean;
}

export interface GlobalSettingsType {
  global_stop_loss_pct: number;
  tacke_profit_pct: number;
  max_trade_allocation_pct: number;
  is_trading_enabled: boolean;
}

export const settingsApi = {
  // --- Watchlist Operations ---
  getWatchlist: async () => {
    const res = await fetch(`${API_URL}/api/settings/watchlist`);
    if (!res.ok) throw new Error('Failed to fetch watchlist');
    return res.json();
  },

  addCompany: async (data: CompanyDataType) => {
    const res = await fetch(`${API_URL}/api/settings/watchlist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to add company');
    return res.json();
  },

  deleteCompany: async (ticker: string) => {
    const res = await fetch(`${API_URL}/api/settings/watchlist/${ticker}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete company');
    return res.json();
  },

  // --- Global Settings Operations ---
  getGlobalSettings: async () => {
    const res = await fetch(`${API_URL}/api/settings/global`);
    if (!res.ok) throw new Error('Failed to fetch global settings');
    return res.json();
  },

  updateGlobalSettings: async (data: GlobalSettingsType) => {
    const res = await fetch(`${API_URL}/api/settings/global`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update settings');
    return res.json();
  },
};