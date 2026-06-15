'use client';

import { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { formatPrice, getDirectionColor } from '@/lib/utils';

export default function HomePage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [scheduler, setScheduler] = useState<any>({ is_running: true, seconds_until_next: 60, in_progress: false });
  const [refreshing, setRefreshing] = useState(false);
  const [countdown, setCountdown] = useState(60);
  const [confidence, setConfidence] = useState<Record<string, any>>({});

  const load = useCallback(() => {
    api.getDashboard().then(setData).catch(console.error).finally(() => setLoading(false));
    api.getSchedulerStatus().then(s => {
      setScheduler(s);
      setCountdown(s.seconds_until_next || 60);
    }).catch(() => {});
  }, []);

  useEffect(() => { load() }, [load]);

  useEffect(() => {
    if (!scheduler.is_running) return;
    const interval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          load();
          return 60;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [scheduler.is_running, load]);

  useEffect(() => {
    if (!data?.watchlist?.items) return;
    data.watchlist.items.forEach((item: any) => {
      api.getDataConfidence(item.ticker).then(c => {
        setConfidence(prev => ({ ...prev, [item.ticker]: c }));
      }).catch(() => {});
    });
  }, [data]);

  const handleRefresh = async () => {
    if (refreshing || scheduler.in_progress) return;
    setRefreshing(true);
    try {
      await api.triggerRefresh();
      load();
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) return <LoadingState />;
  if (!data) return <ErrorState />;

  const canRefresh = !refreshing && !scheduler.in_progress;

  return (
    <div>
      {/* Scheduler Status Bar */}
      <div style={{
        padding: '12px 20px',
        background: 'var(--bg-card)',
        borderRadius: 12,
        border: '1px solid var(--border-color)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
        flexWrap: 'wrap',
        gap: 8,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{
            display: 'inline-block',
            width: 10, height: 10,
            borderRadius: '50%',
            background: scheduler.is_running ? 'var(--color-bullish)' : 'var(--color-bearish)',
          }} />
          <span style={{ fontSize: 14, fontWeight: 500 }}>
            Auto Refresh: {scheduler.is_running ? 'ON' : 'OFF'}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>
            Next in: {countdown}s
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
            {scheduler.last_refresh ? `Last: ${new Date(scheduler.last_refresh).toLocaleTimeString()}` : ''}
          </span>
          <button onClick={handleRefresh} disabled={!canRefresh} style={{
            padding: '6px 14px',
            background: canRefresh ? 'var(--color-info)' : 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: 6,
            color: canRefresh ? '#fff' : 'var(--text-muted)',
            fontSize: 13,
            cursor: canRefresh ? 'pointer' : 'not-allowed',
            opacity: canRefresh ? 1 : 0.5,
          }}>
            {refreshing || scheduler.in_progress ? 'Refreshing...' : 'Refresh Now'}
          </button>
        </div>
      </div>

      {/* Status Cards */}
      <div style={{
        padding: 20,
        background: 'var(--bg-card)',
        borderRadius: 12,
        border: '1px solid var(--border-color)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.02em' }}>Signal Desk</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
            {data.market_hours} · Updated {data.last_updated ? new Date(data.last_updated).toLocaleTimeString() : '--'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 24, textAlign: 'center' }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{data.total_signals}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}>Signals</div>
          </div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700, color: data.health_warnings?.length ? 'var(--color-warning)' : 'var(--color-bullish)' }}>
              {data.health_warnings?.length || 0}
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}>Warnings</div>
          </div>
        </div>
      </div>

      {/* Watchlist */}
      <div style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Watchlist</h2>
        <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
          {data.watchlist?.items?.map((item: any) => {
            const dc = confidence[item.ticker];
            return (
              <a key={item.ticker} href={`/analysis?ticker=${item.ticker}`} style={{
                textDecoration: 'none',
                padding: 16,
                background: 'var(--bg-card)',
                borderRadius: 8,
                border: '1px solid var(--border-color)',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {item.ticker}
                  </span>
                  <span style={{
                    fontSize: 12,
                    padding: '2px 8px',
                    borderRadius: 4,
                    fontWeight: 500,
                    color: getDirectionColor(item.signal_direction),
                    background: `${getDirectionColor(item.signal_direction)}15`,
                  }}>
                    {item.signal_direction || 'neutral'}
                  </span>
                </div>
                <span style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  ${formatPrice(item.price)}
                </span>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                  <span>{item.session || '--'}</span>
                  <span style={{ textTransform: 'capitalize' }}>{item.health_status}</span>
                </div>
                {dc && (
                  <div style={{ fontSize: 11, display: 'flex', gap: 8, color: 'var(--text-muted)' }}>
                    <span>Data Confidence:</span>
                    <span style={{
                      color: dc.score >= 80 ? 'var(--color-bullish)' : dc.score >= 50 ? 'var(--color-warning)' : 'var(--color-bearish)',
                      fontWeight: 600,
                    }}>
                      {dc.score}/100 — {dc.label}
                    </span>
                  </div>
                )}
              </a>
            );
          })}
          {(!data.watchlist?.items || data.watchlist.items.length === 0) && (
            <p style={{ color: 'var(--text-muted)', gridColumn: '1 / -1' }}>
              No tickers in watchlist. <a href="/watchlist" style={{ color: 'var(--color-info)' }}>Add tickers</a>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
      <p style={{ color: 'var(--text-muted)' }}>Loading...</p>
    </div>
  );
}

function ErrorState() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh', flexDirection: 'column', gap: 12 }}>
      <p style={{ color: 'var(--color-bearish)' }}>Failed to load dashboard</p>
      <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
        Ensure the backend is running on port 8000
      </p>
      <button onClick={() => window.location.reload()} style={{
        padding: '8px 16px', background: 'var(--bg-card)',
        border: '1px solid var(--border-color)', borderRadius: 8,
        color: 'var(--text-primary)', fontSize: 14, cursor: 'pointer',
      }}>
        Retry
      </button>
    </div>
  );
}
