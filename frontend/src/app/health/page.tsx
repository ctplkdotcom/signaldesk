'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { formatDate, getHealthColor } from '@/lib/utils';

export default function HealthPage() {
  const [system, setSystem] = useState<any>(null);
  const [warnings, setWarnings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([api.getSystemHealth(), api.getDataHealth()])
      .then(([sys, data]: any) => { setSystem(sys); setWarnings(data.items || []); })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  if (loading) return <p style={{ color: 'var(--text-muted)' }}>Loading...</p>;

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}>Data Health</h1>

      {system && (
        <div style={{
          padding: 20, marginBottom: 24,
          background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border-color)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>System Status</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{system.tickers} tickers tracked</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{
              padding: '4px 12px', borderRadius: 4, fontSize: 13, fontWeight: 600,
              background: system.status === 'healthy' ? 'var(--color-bullish)20' : 'var(--color-warning)20',
              color: system.status === 'healthy' ? 'var(--color-bullish)' : 'var(--color-warning)',
            }}>
              {system.status}
            </div>
            {system.provider && (
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                {system.provider.name}: {system.provider.status} ({system.provider.latency_ms?.toFixed(0)}ms)
              </div>
            )}
          </div>
        </div>
      )}

      {warnings.length > 0 ? (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border-color)', overflow: 'hidden' }}>
          <table>
            <thead>
              <tr><th>Ticker</th><th>Status</th><th>Type</th><th>Message</th><th>Checked</th></tr>
            </thead>
            <tbody>
              {warnings.map((w: any) => (
                <tr key={w.id}>
                  <td style={{ fontWeight: 600 }}>{w.ticker}</td>
                  <td><span style={{ padding: '2px 8px', borderRadius: 3, fontSize: 12, fontWeight: 500, color: getHealthColor(w.status), background: `${getHealthColor(w.status)}15` }}>{w.status}</span></td>
                  <td style={{ color: 'var(--text-secondary)' }}>{w.warning_type}</td>
                  <td style={{ fontSize: 13, color: 'var(--text-muted)' }}>{w.message}</td>
                  <td style={{ fontSize: 13, color: 'var(--text-muted)' }}>{formatDate(w.checked_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ padding: 40, textAlign: 'center', background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border-color)' }}>
          <p style={{ color: 'var(--color-bullish)', fontWeight: 600 }}>All systems healthy</p>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, marginTop: 4 }}>No data quality warnings</p>
        </div>
      )}

      <button onClick={load} style={{
        marginTop: 16, padding: '8px 16px',
        background: 'var(--bg-card)', border: '1px solid var(--border-color)',
        borderRadius: 8, color: 'var(--text-primary)', fontSize: 14, cursor: 'pointer',
      }}>
        Refresh
      </button>
    </div>
  );
}
