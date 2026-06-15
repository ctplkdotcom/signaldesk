const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${res.status}: ${err}`);
  }
  return res.json();
}

export const api = {
  ping: () => fetchJSON<any>('/health'),

  getDashboard: () => fetchJSON<any>('/dashboard'),

  getWatchlist: () => fetchJSON<any>('/dashboard/watchlist'),
  addToWatchlist: (ticker: string) =>
    fetchJSON<any>(`/dashboard/watchlist/${ticker}`, { method: 'POST' }),
  removeFromWatchlist: (ticker: string) =>
    fetchJSON<any>(`/dashboard/watchlist/${ticker}`, { method: 'DELETE' }),

  listTickers: () => fetchJSON<any>('/tickers'),
  getTicker: (ticker: string) => fetchJSON<any>(`/tickers/${ticker}`),
  getTickerPrice: (ticker: string) => fetchJSON<any>(`/tickers/${ticker}/price`),
  getTickerBars: (ticker: string, params?: string) =>
    fetchJSON<any>(`/tickers/${ticker}/bars${params ? '?' + params : ''}`),
  getTickerSignals: (ticker: string) => fetchJSON<any>(`/tickers/${ticker}/signals`),
  getTickerHealth: (ticker: string) => fetchJSON<any>(`/tickers/${ticker}/health`),
  getTickerDecisionSummary: (ticker: string) =>
    fetchJSON<any>(`/tickers/${ticker}/decision-summary`),
  getTickerVerification: (ticker: string) => fetchJSON<any>(`/tickers/${ticker}/verification`),
  refreshTicker: (ticker: string) =>
    fetchJSON<any>(`/tickers/${ticker}/refresh`, { method: 'POST' }),

  getNews: (ticker?: string) =>
    fetchJSON<any>(`/news${ticker ? '?ticker=' + ticker : ''}`),
  postNews: (data: any) =>
    fetchJSON<any>('/news', { method: 'POST', body: JSON.stringify(data) }),
  ingestNews: (ticker?: string) =>
    fetchJSON<any>(`/news/ingest${ticker ? '?ticker=' + ticker : ''}`, { method: 'POST' }),

  getSignals: (ticker?: string) =>
    fetchJSON<any>(`/signals${ticker ? '?ticker=' + ticker : ''}`),

  getSystemHealth: () => fetchJSON<any>('/health'),
  getDataHealth: () => fetchJSON<any>('/health/data'),

  // ── New endpoints ──────────────────────────────────────────────────────

  getSchedulerStatus: () => fetchJSON<any>('/scheduler/status'),
  triggerRefresh: (ticker?: string) =>
    fetchJSON<any>(`/scheduler/refresh${ticker ? '?ticker=' + ticker : ''}`, { method: 'POST' }),

  getActivityLog: (params?: string) =>
    fetchJSON<any>(`/activity-log${params ? '?' + params : ''}`),

  getDataConfidence: (ticker: string) =>
    fetchJSON<any>(`/data-confidence/${ticker}`),

  getShortTermIndicators: (ticker: string) =>
    fetchJSON<any>(`/indicators/${ticker}`),

  runBacktest: (ticker: string, strategy?: string) =>
    fetchJSON<any>(`/backtest/run?ticker=${ticker}${strategy ? '&strategy=' + strategy : ''}`, { method: 'POST' }),

  listBacktestRuns: () => fetchJSON<any>('/backtest/runs'),
  getBacktestRun: (runId: number) => fetchJSON<any>(`/backtest/runs/${runId}`),

  listMethodologies: () => fetchJSON<any>('/methodologies'),
  getMethodology: (name: string) => fetchJSON<any>(`/methodologies/${encodeURIComponent(name)}`),

  runRetentionCleanup: () =>
    fetchJSON<any>('/retention/cleanup', { method: 'POST' }),
};
