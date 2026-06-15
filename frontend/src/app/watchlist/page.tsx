'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { formatPrice, formatDate, getDirectionColor, getHealthColor } from '@/lib/utils';

export default function WatchlistPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [addTicker, setAddTicker] = useState('');

  const loadWatchlist = () => {
    setLoading(true);
    api.getWatchlist()
      .then((d: any) => setItems(d.items || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadWatchlist(); }, []);

  const handleAdd = async () => {
    if (!addTicker.trim()) return;
    try {
      await api.addToWatchlist(addTicker.trim().toUpperCase());
      setAddTicker('');
      loadWatchlist();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleRemove = async (ticker: string) => {
    try {
      await api.removeFromWatchlist(ticker);
      loadWatchlist();
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700 }}>Watchlist</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            placeholder="Add ticker (e.g. AAPL)"
            value={addTicker}
            onChange={e => setAddTicker(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === 'Enter' && handleAdd()}
            style={{ width: 200 }}
          />
          <button onClick={handleAdd} style={{
            padding: '8px 16px',
            background: 'var(--color-info)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--border-radius)',
            fontSize: 14,
            fontWeight: 500,
          }}>
            Add
          </button>
        </div>
      </div>

      {loading ? (
        <p style={{ color: 'var(--text-muted)' }}>Loading...</p>
      ) : items.length === 0 ? (
        <div style={{
          padding: 40,
          textAlign: 'center',
          background: 'var(--bg-card)',
          borderRadius: 'var(--border-radius-lg)',
          border: '1px solid var(--border-color)',
        }}>
          <p style={{ color: 'var(--text-muted)', fontSize: 16 }}>Your watchlist is empty</p>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 8 }}>
            Add tickers like MU, VOO, or SNDK to get started
          </p>
        </div>
      ) : (
        <div style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--border-radius-lg)',
          border: '1px solid var(--border-color)',
          overflow: 'hidden',
        }}>
          <table>
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Name</th>
                <th>Close</th>
                <th>Price</th>
                <th>Session</th>
                <th>Signal</th>
                <th>Health</th>
                <th>Price Time</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item: any) => (
                <tr key={item.ticker}>
                  <td>
                    <Link href={`/analysis?ticker=${item.ticker}`} style={{
                      fontWeight: 600, color: 'var(--text-primary)', textDecoration: 'none',
                    }}>
                      {item.ticker}
                    </Link>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{item.name}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-muted)' }}>
                    ${formatPrice(item.previous_close)}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                    ${formatPrice(item.price)}
                  </td>
                  <td style={{ fontSize: 13 }}>{item.session}</td>
                  <td>
                    <span style={{
                      color: getDirectionColor(item.signal_direction),
                      fontSize: 13,
                      fontWeight: 500,
                    }}>
                      {item.signal_direction || 'neutral'}
                    </span>
                  </td>
                  <td>
                    <span style={{
                      color: getHealthColor(item.health_status),
                      fontSize: 13,
                    }}>
                      {item.health_status}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                    {item.updated_et ? formatDate(item.updated_et) : '--'}
                  </td>
                  <td>
                    <button
                      onClick={() => handleRemove(item.ticker)}
                      style={{
                        padding: '4px 12px',
                        background: 'transparent',
                        border: '1px solid var(--color-bearish)',
                        borderRadius: 4,
                        color: 'var(--color-bearish)',
                        fontSize: 12,
                      }}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
