'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { formatDate, scoreToLabel } from '@/lib/utils';

export default function NewsPage() {
  const [news, setNews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [ingesting, setIngesting] = useState(false);

  const loadNews = () => {
    setLoading(true);
    api.getNews(filter || undefined)
      .then((d: any) => setNews(d.items || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadNews(); }, [filter]);

  const handleIngest = async () => {
    setIngesting(true);
    try {
      await api.ingestNews(filter || undefined);
      loadNews();
    } catch (e: any) {
      alert(e.message);
    }
    setIngesting(false);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700 }}>News Signals</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            placeholder="Filter by ticker"
            value={filter}
            onChange={e => setFilter(e.target.value.toUpperCase())}
            style={{ width: 150 }}
          />
          <button
            onClick={handleIngest}
            disabled={ingesting}
            style={{
              padding: '8px 16px',
              background: ingesting ? 'var(--text-muted)' : 'var(--color-info)',
              color: '#fff',
              border: 'none',
              borderRadius: 'var(--border-radius)',
              fontSize: 14,
              fontWeight: 500,
            }}
          >
            {ingesting ? 'Loading...' : 'Ingest News'}
          </button>
        </div>
      </div>

      {loading ? (
        <p style={{ color: 'var(--text-muted)' }}>Loading news...</p>
      ) : news.length === 0 ? (
        <div style={{
          padding: 40,
          textAlign: 'center',
          background: 'var(--bg-card)',
          borderRadius: 'var(--border-radius-lg)',
          border: '1px solid var(--border-color)',
        }}>
          <p style={{ color: 'var(--text-muted)' }}>No news articles found</p>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 8 }}>
            Click "Ingest News" to fetch latest articles
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {news.map((article: any) => {
            const score = article.score;
            const label = score ? scoreToLabel(score.final) : null;
            return (
              <div key={article.id} style={{
                padding: 16,
                background: 'var(--bg-card)',
                borderRadius: 'var(--border-radius)',
                border: '1px solid var(--border-color)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                gap: 16,
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>
                    {article.title}
                  </div>
                  <div style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)', display: 'flex', gap: 12 }}>
                    <span>{article.source}</span>
                    <span>{article.event_type}</span>
                    <span>{formatDate(article.published_utc)}</span>
                  </div>
                  {score?.explanation && (
                    <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>
                      {score.explanation}
                    </div>
                  )}
                </div>
                {score && (
                  <div style={{
                    textAlign: 'center',
                    padding: '6px 14px',
                    borderRadius: 6,
                    background: `${label?.color || 'var(--color-neutral)'}15`,
                    border: `1px solid ${label?.color || 'var(--color-neutral)'}30`,
                    minWidth: 90,
                  }}>
                    <div style={{
                      fontSize: 16,
                      fontWeight: 700,
                      color: label?.color || 'var(--color-neutral)',
                    }}>
                      {score.final?.toFixed(0)}
                    </div>
                    <div style={{
                      fontSize: 11,
                      color: label?.color || 'var(--color-neutral)',
                      marginTop: 2,
                      fontWeight: 500,
                    }}>
                      {label?.label || 'Neutral'}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
