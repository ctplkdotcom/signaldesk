'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function ActivityLogPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getActivityLog().then(r => setLogs(r.items || [])).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: 48 }}>Loading...</p>;

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>Activity Log</h1>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {logs.length === 0 && (
          <p style={{ color: 'var(--text-muted)' }}>No activity recorded yet.</p>
        )}
        {logs.map((log: any) => (
          <div key={log.id} style={{
            padding: '10px 14px',
            background: 'var(--bg-card)',
            borderRadius: 6,
            border: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 12,
            fontSize: 13,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0 }}>
              <span style={{
                padding: '2px 6px',
                borderRadius: 4,
                fontSize: 11,
                fontWeight: 600,
                background: log.level === 'ERROR' ? 'var(--color-bearish)15' : log.level === 'WARNING' ? 'var(--color-warning)15' : 'transparent',
                color: log.level === 'ERROR' ? 'var(--color-bearish)' : log.level === 'WARNING' ? 'var(--color-warning)' : 'var(--text-muted)',
                flexShrink: 0,
              }}>
                {log.level}
              </span>
              <span style={{ color: 'var(--text-muted)', flexShrink: 0, fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '--'}
              </span>
              {log.ticker && (
                <span style={{
                  padding: '1px 6px',
                  borderRadius: 4,
                  background: 'var(--color-info)15',
                  color: 'var(--color-info)',
                  fontSize: 12,
                  fontWeight: 600,
                  flexShrink: 0,
                }}>
                  {log.ticker}
                </span>
              )}
              <span style={{ color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {log.action}
              </span>
              {log.message && (
                <span style={{ color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  — {log.message}
                </span>
              )}
            </div>
            {log.duration_ms && (
              <span style={{ color: 'var(--text-muted)', fontSize: 12, flexShrink: 0 }}>
                {log.duration_ms}ms
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
