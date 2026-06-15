'use client';

import { getDirectionColor, getHealthColor, formatPrice } from '@/lib/utils';

interface DecisionSummary {
  ticker: string;
  overall_direction: string;
  composite_confidence: number;
  explanation: string;
  signal: {
    direction: string;
    confidence: number;
    explanation: string | null;
  } | null;
  data_health: {
    status: string;
    warning_type: string | null;
    message: string | null;
  } | null;
  news_sentiment_avg: number;
  news_article_count: number;
  current_price: number | null;
  price_updated_utc: string | null;
}

function confidenceBar(value: number): string {
  const pct = Math.max(0, Math.min(100, value * 100));
  if (pct >= 70) return `linear-gradient(90deg, var(--color-bullish) ${pct}%, var(--bg-tertiary) ${pct}%)`;
  if (pct >= 40) return `linear-gradient(90deg, var(--color-warning) ${pct}%, var(--bg-tertiary) ${pct}%)`;
  return `linear-gradient(90deg, var(--color-bearish) ${pct}%, var(--bg-tertiary) ${pct}%)`;
}

function sentimentLabel(avg: number): string {
  if (avg > 0) return 'Positive';
  if (avg < 0) return 'Negative';
  return 'Neutral';
}

function sentimentColor(avg: number): string {
  if (avg > 0) return 'var(--color-bullish)';
  if (avg < 0) return 'var(--color-bearish)';
  return 'var(--color-neutral)';
}

export default function DecisionSummaryCard({ summary }: { summary: DecisionSummary }) {
  const confPct = (summary.composite_confidence * 100).toFixed(0);
  const dirColor = getDirectionColor(summary.overall_direction);

  return (
    <div style={{
      padding: 20,
      background: 'var(--bg-card)',
      borderRadius: 12,
      border: '1px solid var(--border-color)',
      marginBottom: 16,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>
          Decision Summary
        </h3>
        <span style={{
          marginLeft: 'auto',
          padding: '4px 12px', borderRadius: 4, fontSize: 13, fontWeight: 600,
          color: dirColor,
          background: `${dirColor}20`,
        }}>
          {summary.overall_direction.toUpperCase()}
        </span>
      </div>

      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
          <span>Composite Confidence</span>
          <span>{confPct}%</span>
        </div>
        <div style={{
          height: 8, borderRadius: 4,
          background: confidenceBar(summary.composite_confidence),
          transition: 'background 0.3s',
        }} />
      </div>

      <div style={{
        padding: 12, borderRadius: 8, marginBottom: 16, fontSize: 13,
        background: `${dirColor}08`,
        border: `1px solid ${dirColor}30`,
        color: 'var(--text-secondary)', lineHeight: 1.6,
      }}>
        {summary.explanation}
      </div>

      <div style={{ display: 'flex', gap: 16, fontSize: 13, color: 'var(--text-secondary)' }}>
        <div style={{ flex: 1 }}>
          <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 4 }}>Signal</div>
          <div style={{ fontWeight: 600, color: getDirectionColor(summary.signal?.direction || 'neutral') }}>
            {summary.signal ? summary.signal.direction.toUpperCase() + ' (' + (summary.signal.confidence * 100).toFixed(0) + '%)' : 'None'}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 4 }}>Data Health</div>
          <div style={{ fontWeight: 600, color: getHealthColor(summary.data_health?.status || 'unknown') }}>
            {summary.data_health?.status || 'Unknown'}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 4 }}>News Sentiment</div>
          <div style={{ fontWeight: 600, color: sentimentColor(summary.news_sentiment_avg) }}>
            {summary.news_article_count > 0
              ? `${sentimentLabel(summary.news_sentiment_avg)} (${summary.news_article_count})`
              : 'No news'}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 4 }}>Price</div>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
            {summary.current_price != null ? `$${formatPrice(summary.current_price)}` : '--'}
          </div>
        </div>
      </div>
    </div>
  );
}
