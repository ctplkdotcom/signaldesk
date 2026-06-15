'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function MethodologiesPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any>(null);

  useEffect(() => {
    api.listMethodologies().then(r => setItems(r.items || [])).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: 48 }}>Loading...</p>;

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>Methodology Library</h1>

      {selected ? (
        <div>
          <button onClick={() => setSelected(null)} style={{
            padding: '6px 12px', marginBottom: 16, background: 'var(--bg-card)',
            border: '1px solid var(--border-color)', borderRadius: 6,
            color: 'var(--text-primary)', cursor: 'pointer', fontSize: 13,
          }}>&larr; Back to list</button>
          <div style={{
            padding: 20, background: 'var(--bg-card)', borderRadius: 12,
            border: '1px solid var(--border-color)',
          }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 4 }}>{selected.name}</h2>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>Version {selected.version}</p>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.5 }}>{selected.description}</p>

            {selected.input_data && (
              <Section title="Input Data" content={selected.input_data} />
            )}
            {selected.formula && (
              <div style={{ marginBottom: 16 }}>
                <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>Formula</h3>
                <code style={{ padding: '8px 12px', background: 'var(--bg-primary)', borderRadius: 6, display: 'block', fontSize: 13 }}>
                  {selected.formula}
                </code>
              </div>
            )}
            {selected.assumptions && (
              <Section title="Assumptions" content={selected.assumptions} />
            )}
            {selected.limitations && (
              <Section title="Limitations" content={selected.limitations} />
            )}
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {items.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No methodologies found.</p>}
          {items.map((m: any) => (
            <div key={m.name} onClick={() => setSelected(m)} style={{
              padding: 16, background: 'var(--bg-card)', borderRadius: 8,
              border: '1px solid var(--border-color)', cursor: 'pointer',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <span style={{ fontSize: 15, fontWeight: 600 }}>{m.name}</span>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>v{m.version}</span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.4 }}>{m.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Section({ title, content }: { title: string; content: any }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>{title}</h3>
      <div style={{ padding: '8px 12px', background: 'var(--bg-primary)', borderRadius: 6, fontSize: 13, color: 'var(--text-secondary)' }}>
        {typeof content === 'object' ? (
          Object.entries(content).map(([k, v]) => (
            <div key={k} style={{ marginBottom: 2 }}>
              <span style={{ fontWeight: 500 }}>{k}:</span> {String(v)}
            </div>
          ))
        ) : (
          <span>{content}</span>
        )}
      </div>
    </div>
  );
}
