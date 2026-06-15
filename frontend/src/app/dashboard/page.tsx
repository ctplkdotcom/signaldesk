'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { formatPrice, getDirectionColor, formatDate } from '@/lib/utils';

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboard().then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ color: 'var(--text-muted)' }}>Loading...</p>;
  if (!data) return <p style={{ color: 'var(--text-muted)' }}>No data</p>;

  return (
    <div>
      <div style={{
        padding: 16, marginBottom: 24,
        background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border-color)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ color: 'var(--text-secondary)' }}>{data.market_hours}</span>
        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>
          Updated: {data.last_updated ? new Date(data.last_updated).toLocaleTimeString() : '--'}
        </span>
      </div>

      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Watchlist</h2>
      <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))' }}>
        {data.watchlist?.items?.map((item: any) => (
          <Link key={item.ticker} href={`/analysis?ticker=${item.ticker}`} style={{
            textDecoration: 'none', padding: 16,
            background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border-color)',
          }}>
            <div style={{ fontWeight: 600 }}>{item.ticker}</div>
            <div style={{ fontSize: 22, fontWeight: 700, fontFamily: 'var(--font-mono)', marginTop: 4 }}>
              ${formatPrice(item.price)}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
              {item.session} · {item.health_status}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
