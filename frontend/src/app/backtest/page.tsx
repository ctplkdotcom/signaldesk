'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function BacktestPage() {
  const [ticker, setTicker] = useState('MU');
  const [strategy, setStrategy] = useState('momentum_5m');
  const [result, setResult] = useState<any>(null);
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.listBacktestRuns().then(r => setRuns(r.items || [])).catch(() => {});
  }, []);

  const run = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await api.runBacktest(ticker, strategy);
      setResult(res);
      api.listBacktestRuns().then(r => setRuns(r.items || [])).catch(() => {});
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>Backtest Lab</h1>

      <div style={{
        padding: 16,
        background: 'var(--bg-card)',
        borderRadius: 12,
        border: '1px solid var(--border-color)',
        marginBottom: 20,
        display: 'flex',
        gap: 12,
        alignItems: 'flex-end',
        flexWrap: 'wrap',
      }}>
        <div>
          <label style={{ display: 'block', fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Ticker</label>
          <input value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())} style={{
            padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border-color)',
            background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: 14, width: 100,
          }} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Strategy</label>
          <select value={strategy} onChange={e => setStrategy(e.target.value)} style={{
            padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border-color)',
            background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: 14,
          }}>
            <option value="momentum_5m">5-min Momentum</option>
            <option value="vwap_reversion">VWAP Reversion</option>
          </select>
        </div>
        <button onClick={run} disabled={loading} style={{
          padding: '8px 20px', borderRadius: 6, border: 'none',
          background: loading ? 'var(--text-muted)' : 'var(--color-info)',
          color: '#fff', fontSize: 14, cursor: loading ? 'not-allowed' : 'pointer',
        }}>
          {loading ? 'Running...' : 'Run Backtest'}
        </button>
      </div>

      {error && (
        <div style={{ padding: 12, background: 'var(--color-bearish)15', borderRadius: 8, marginBottom: 16, color: 'var(--color-bearish)', fontSize: 14 }}>
          {error}
        </div>
      )}

      {result && result.total_return_pct !== undefined && (
        <div style={{
          padding: 20, background: 'var(--bg-card)', borderRadius: 12,
          border: '1px solid var(--border-color)', marginBottom: 20,
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Results for {result.ticker} — {result.strategy}</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 }}>
            <Metric label="Total Return" value={`${result.total_return_pct}%`} color={result.total_return_pct >= 0 ? 'var(--color-bullish)' : 'var(--color-bearish)'} />
            <Metric label="Trades" value={String(result.num_trades)} />
            <Metric label="Win Rate" value={`${(result.win_rate * 100).toFixed(1)}%`} />
            <Metric label="Avg Win" value={`${result.avg_win}%`} color="var(--color-bullish)" />
            <Metric label="Avg Loss" value={`${result.avg_loss}%`} color="var(--color-bearish)" />
            <Metric label="Profit Factor" value={String(result.profit_factor)} />
            <Metric label="Max Drawdown" value={`${result.max_drawdown_pct}%`} color="var(--color-bearish)" />
            <Metric label="Avg Hold" value={`${result.avg_holding_bars} bars`} />
            <Metric label="Bars Used" value={String(result.bars_used)} />
            <Metric label="Slippage" value={`${(result.slippage_assumption * 100).toFixed(1)}%`} />
            <Metric label="Fee" value={`${(result.fee_assumption * 100).toFixed(1)}%`} />
          </div>
          {result.num_trades > 0 && (
            <details style={{ marginTop: 16 }}>
              <summary style={{ cursor: 'pointer', fontSize: 13, color: 'var(--text-secondary)' }}>
                Trade Log ({result.num_trades} trades)
              </summary>
              <div style={{ marginTop: 8, fontSize: 12, maxHeight: 300, overflowY: 'auto' }}>
                {(result.trade_log || []).map((t: any, i: number) => (
                  <div key={i} style={{
                    padding: '6px 8px', borderBottom: '1px solid var(--border-color)',
                    display: 'flex', gap: 16, color: 'var(--text-secondary)',
                  }}>
                    <span>#{i + 1}</span>
                    <span>Entry: ${t.entry_price}</span>
                    <span>Exit: ${t.exit_price}</span>
                    <span style={{ color: t.net_return_pct >= 0 ? 'var(--color-bullish)' : 'var(--color-bearish)' }}>
                      {t.net_return_pct}%
                    </span>
                    <span>{t.holding_bars} bars</span>
                  </div>
                ))}
              </div>
            </details>
          )}
        </div>
      )}

      {result && result.error && (
        <div style={{ padding: 12, background: 'var(--color-bearish)15', borderRadius: 8, color: 'var(--color-bearish)', fontSize: 14 }}>
          {result.error}
        </div>
      )}

      {runs.length > 0 && (
        <div>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Previous Runs</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {runs.slice(0, 10).map((r: any) => (
              <div key={r.run_id} style={{
                padding: '8px 12px', background: 'var(--bg-card)',
                borderRadius: 6, border: '1px solid var(--border-color)',
                fontSize: 13, display: 'flex', gap: 12, color: 'var(--text-secondary)',
              }}>
                <span>Run #{r.run_id}</span>
                <span>{r.strategy}</span>
                <span style={{
                  color: r.status === 'completed' ? 'var(--color-bullish)' : 'var(--color-bearish)',
                }}>{r.status}</span>
                <span>{r.created_at ? new Date(r.created_at).toLocaleString() : ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ padding: '10px 12px', background: 'var(--bg-primary)', borderRadius: 8, border: '1px solid var(--border-color)' }}>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: color || 'var(--text-primary)' }}>{value}</div>
    </div>
  );
}
