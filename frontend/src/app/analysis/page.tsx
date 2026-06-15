'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { formatPrice, formatDate, getDirectionColor } from '@/lib/utils';
import VerificationMenu from '@/components/VerificationMenu';
import DecisionSummaryCard from '@/components/DecisionSummaryCard';

export default function AnalysisPage() {
  return (
    <Suspense fallback={<p style={{color:'var(--text-muted)'}}>Loading...</p>}>
      <AnalysisContent />
    </Suspense>
  );
}

function AnalysisContent() {
  const searchParams = useSearchParams();
  const ticker = searchParams.get('ticker') || 'MU';
  const [tab, setTab] = useState<'overview' | 'bars' | 'signals'>('overview');
  const [price, setPrice] = useState<any>(null);
  const [bars, setBars] = useState<any[]>([]);
  const [signals, setSignals] = useState<any[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [verification, setVerification] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [indicators, setIndicators] = useState<any>(null);
  const [confidence, setConfidence] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = () => {
    setLoading(true);
    Promise.all([
      api.getTickerPrice(ticker).catch(() => null),
      api.getTickerBars(ticker).catch(() => ({ items: [] })),
      api.getTickerSignals(ticker).catch(() => ({ items: [] })),
      api.getTickerHealth(ticker).catch(() => null),
      api.getTickerVerification(ticker).catch(() => null),
      api.getTickerDecisionSummary(ticker).catch(() => null),
      api.getShortTermIndicators(ticker).catch(() => null),
      api.getDataConfidence(ticker).catch(() => null),
    ])
    .then(([p, b, s, h, v, d, ind, conf]) => {
      setPrice(p);
      setBars(b.items || []);
      setSignals(s.items || []);
      setHealth(h);
      setVerification(v);
      setSummary(d);
      setIndicators(ind);
      setConfidence(conf);
    })
    .catch(console.error)
    .finally(() => setLoading(false));
  };

  useEffect(() => { load() }, [ticker]);

  const handleRefresh = async () => {
    if (refreshing) return;
    setRefreshing(true);
    try {
      await api.triggerRefresh(ticker);
      load();
    } catch (e) { console.error(e) }
    finally { setRefreshing(false) }
  };

  if (loading) return <p style={{ color: 'var(--text-muted)' }}>Loading {ticker}...</p>;

  const signal = price?.signal;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700 }}>{ticker}</h1>
        <span style={{ fontSize: 28, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
          ${formatPrice(price?.price)}
        </span>
        {signal && (
          <span style={{
            padding: '4px 12px', borderRadius: 4, fontSize: 13, fontWeight: 600,
            color: getDirectionColor(signal.direction),
            background: `${getDirectionColor(signal.direction)}20`,
          }}>
            {signal.direction?.toUpperCase()} ({(signal.confidence * 100).toFixed(0)}%)
          </span>
        )}
        {health && (
          <span style={{
            padding: '4px 12px', borderRadius: 4, fontSize: 12,
            background: health.status === 'healthy' ? 'var(--color-bullish)20' : 'var(--color-warning)20',
            color: health.status === 'healthy' ? 'var(--color-bullish)' : 'var(--color-warning)',
          }}>
            {health.status}
          </span>
        )}
        <button onClick={handleRefresh} disabled={refreshing} style={{
          marginLeft: 'auto', padding: '6px 14px', borderRadius: 6, border: '1px solid var(--border-color)',
          background: refreshing ? 'var(--bg-card)' : 'var(--color-info)', color: refreshing ? 'var(--text-muted)' : '#fff',
          fontSize: 13, cursor: refreshing ? 'not-allowed' : 'pointer',
        }}>
          {refreshing ? 'Refreshing...' : 'Refresh Now'}
        </button>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, fontSize: 13, color: 'var(--text-secondary)' }}>
        <span>Provider: {price?.provider || 'Polygon.io'}</span>
        <span>·</span>
        <span>Last updated: {price?.updated_et ? new Date(price.updated_et).toLocaleString() : '--'}</span>
        <span>·</span>
        <span>Session: {price?.session || '--'}</span>
        {confidence && (
          <>
            <span>·</span>
            <span style={{ fontWeight: 500, color: confidence.score >= 80 ? 'var(--color-bullish)' : confidence.score >= 50 ? 'var(--color-warning)' : 'var(--color-bearish)' }}>
              Data: {confidence.score}/100
            </span>
          </>
        )}
        <span style={{ marginLeft: 'auto' }}>
          {verification && (
            <VerificationMenu
              ticker={ticker}
              links={verification.verification_links || []}
              preferredSource={verification.preferred_verification_source}
              supported={verification.verification_supported}
            />
          )}
        </span>
      </div>

      {indicators && indicators.short_term_direction && (
        <div style={{
          padding: 12, marginBottom: 16, borderRadius: 8, fontSize: 13,
          background: indicators.short_term_direction === 'Short-Term Bullish' ? 'var(--color-bullish)10'
            : indicators.short_term_direction === 'Short-Term Bearish' ? 'var(--color-bearish)10'
            : 'var(--bg-card)',
          border: `1px solid var(--border-color)`,
          display: 'flex', gap: 20, flexWrap: 'wrap',
        }}>
          <div>
            <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>Short-Term Signal</span>
            <div style={{
              fontWeight: 600, fontSize: 14, marginTop: 2,
              color: indicators.short_term_direction === 'Short-Term Bullish' ? 'var(--color-bullish)'
                : indicators.short_term_direction === 'Short-Term Bearish' ? 'var(--color-bearish)'
                : 'var(--text-secondary)',
            }}>{indicators.short_term_direction}</div>
          </div>
          {indicators.change_1m_pct !== undefined && (
            <>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>1-min</span>
                <div style={{ fontWeight: 600, fontSize: 14, marginTop: 2, color: indicators.change_1m_pct >= 0 ? 'var(--color-bullish)' : 'var(--color-bearish)' }}>
                  {indicators.change_1m_pct > 0 ? '+' : ''}{indicators.change_1m_pct}%
                </div>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>5-min</span>
                <div style={{ fontWeight: 600, fontSize: 14, marginTop: 2, color: indicators.change_5m_pct >= 0 ? 'var(--color-bullish)' : 'var(--color-bearish)' }}>
                  {indicators.change_5m_pct > 0 ? '+' : ''}{indicators.change_5m_pct}%
                </div>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>10-min</span>
                <div style={{ fontWeight: 600, fontSize: 14, marginTop: 2, color: indicators.change_10m_pct >= 0 ? 'var(--color-bullish)' : 'var(--color-bearish)' }}>
                  {indicators.change_10m_pct > 0 ? '+' : ''}{indicators.change_10m_pct}%
                </div>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>VWAP Distance</span>
                <div style={{ fontWeight: 600, fontSize: 14, marginTop: 2, color: indicators.vwap_distance_pct !== null && indicators.vwap_distance_pct >= 0 ? 'var(--color-bullish)' : 'var(--color-bearish)' }}>
                  {indicators.vwap_distance_pct !== null ? `${indicators.vwap_distance_pct > 0 ? '+' : ''}${indicators.vwap_distance_pct}%` : '--'}
                </div>
              </div>
              {indicators.volume_spike_5m_pct !== null && (
                <div>
                  <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>Vol Spike (5m)</span>
                  <div style={{ fontWeight: 600, fontSize: 14, marginTop: 2, color: indicators.volume_spike_5m_pct > 0 ? 'var(--color-bullish)' : 'var(--text-secondary)' }}>
                    {indicators.volume_spike_5m_pct > 0 ? '+' : ''}{indicators.volume_spike_5m_pct}%
                  </div>
                </div>
              )}
            </>
          )}
          {indicators.status === 'insufficient_data' && (
            <span style={{ color: 'var(--color-warning)' }}>Insufficient intraday data for short-term analysis</span>
          )}
        </div>
      )}

      <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        <div style={{ padding: 16, background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border-color)', flex: 1 }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>O / H / L</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14 }}>
            {formatPrice(price?.open)} / {formatPrice(price?.high)} / {formatPrice(price?.low)}
          </div>
        </div>
        <div style={{ padding: 16, background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border-color)', flex: 1 }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>Bid / Ask</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14 }}>
            {formatPrice(price?.bid)} / {formatPrice(price?.ask)}
          </div>
        </div>
        <div style={{ padding: 16, background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border-color)', flex: 1 }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>Volume / Session</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14 }}>
            {(price?.volume || 0).toLocaleString()} · {price?.session || '--'}
          </div>
        </div>
      </div>

      {summary && <DecisionSummaryCard summary={summary} />}

      {signal?.explanation && (
        <div style={{
          padding: 12, marginBottom: 16,
          background: signal.direction === 'bullish' ? 'var(--color-bullish)08' : 'var(--color-bearish)08',
          border: `1px solid ${getDirectionColor(signal.direction)}30`,
          borderRadius: 8, fontSize: 13, color: 'var(--text-secondary)',
        }}>
          <strong>MA Trend Signal:</strong> {signal.explanation}
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, borderBottom: '1px solid var(--border-color)' }}>
        {['overview', 'bars', 'signals'].map(t => (
          <button key={t} onClick={() => setTab(t as any)} style={{
            padding: '8px 16px', background: 'transparent', border: 'none',
            borderBottom: tab === t ? '2px solid var(--color-info)' : '2px solid transparent',
            color: tab === t ? 'var(--text-primary)' : 'var(--text-secondary)',
            fontWeight: tab === t ? 600 : 400, fontSize: 14, cursor: 'pointer',
          }}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div style={{ padding: 20, background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border-color)' }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>Data Quality</h3>
          {health ? (
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              <p>Status: <strong style={{ color: health.status === 'healthy' ? 'var(--color-bullish)' : 'var(--color-warning)' }}>{health.status}</strong></p>
              {health.warning_type && <p>Warning: {health.warning_type}</p>}
              {health.message && <p style={{ marginTop: 4, fontSize: 13, color: 'var(--text-muted)' }}>{health.message}</p>}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No health data</p>
          )}
          {confidence && (
            <>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginTop: 16, marginBottom: 8 }}>Data Confidence</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 120, height: 8, borderRadius: 4, background: 'var(--bg-primary)', overflow: 'hidden',
                }}>
                  <div style={{
                    width: `${confidence.score}%`, height: '100%',
                    background: confidence.score >= 80 ? 'var(--color-bullish)' : confidence.score >= 50 ? 'var(--color-warning)' : 'var(--color-bearish)',
                    borderRadius: 4, transition: 'width 0.3s',
                  }} />
                </div>
                <span style={{ fontWeight: 600, fontSize: 14, color: confidence.score >= 80 ? 'var(--color-bullish)' : confidence.score >= 50 ? 'var(--color-warning)' : 'var(--color-bearish)' }}>
                  {confidence.score}/100
                </span>
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{confidence.label}</span>
              </div>
              {confidence.breakdown?.length > 0 && (
                <div style={{ marginTop: 8, fontSize: 12, color: 'var(--color-warning)' }}>
                  {confidence.breakdown.map((b: any, i: number) => (
                    <div key={i}>-{b.penalty} for {b.reason}</div>
                  ))}
                </div>
              )}
            </>
          )}
          <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginTop: 16, marginBottom: 8 }}>Provider</h3>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)' }}>Polygon.io · {price?.updated_et ? new Date(price.updated_et).toLocaleString() : '--'}</p>
        </div>
      )}

      {tab === 'bars' && (
        <div style={{ padding: 20, background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border-color)' }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 12 }}>
            Price Bars ({bars.length})
          </h3>
          <table>
            <thead>
              <tr>
                <th>Time (ET)</th><th>Session</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th>
              </tr>
            </thead>
            <tbody>
              {bars.slice(-50).reverse().map((b: any, i: number) => (
                <tr key={i}>
                  <td style={{ fontSize: 13 }}>{formatDate(b.timestamp_et)}</td>
                  <td style={{ fontSize: 12 }}>{b.session}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{formatPrice(b.open)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{formatPrice(b.high)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{formatPrice(b.low)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{formatPrice(b.close)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>{(b.volume || 0).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'signals' && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border-color)', overflow: 'hidden' }}>
          {signals.length === 0 ? (
            <p style={{ padding: 20, color: 'var(--text-muted)' }}>No signals yet.</p>
          ) : (
            <table>
              <thead>
                <tr><th>Time</th><th>Strategy</th><th>Direction</th><th>Confidence</th><th>Explanation</th></tr>
              </thead>
              <tbody>
                {signals.map((s: any) => (
                  <tr key={s.id}>
                    <td style={{ fontSize: 13 }}>{formatDate(s.generated_at)}</td>
                    <td style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{s.strategy_type}</td>
                    <td style={{ color: getDirectionColor(s.direction), fontWeight: 600 }}>{s.direction}</td>
                    <td>{(s.confidence * 100).toFixed(0)}%</td>
                    <td style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 300 }}>{s.explanation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
