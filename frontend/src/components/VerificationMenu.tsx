'use client';

import { useState, useRef, useEffect } from 'react';

interface LinkItem {
  source: string;
  url: string;
}

interface Props {
  ticker: string;
  links: LinkItem[];
  preferredSource?: string | null;
  supported: boolean;
}

export default function VerificationMenu({ ticker, links, preferredSource, supported }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  if (!supported || links.length === 0) {
    return (
      <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
        No external verification links available for {ticker}
      </div>
    );
  }

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          padding: '8px 16px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: 8,
          color: 'var(--text-primary)',
          fontSize: 13,
          cursor: 'pointer',
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
          <polyline points="15 3 21 3 21 9" />
          <line x1="10" y1="14" x2="21" y2="3" />
        </svg>
        Verify on Website
      </button>

      {open && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            right: 0,
            width: 280,
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: 10,
            boxShadow: 'var(--shadow-lg)',
            zIndex: 50,
            padding: 12,
          }}
        >
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 10, lineHeight: 1.4 }}>
            Verify this quote on an external market page. External sites may use different data feeds or delayed quotes. Compare ticker, time, session, and price context.
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {links.map((link) => (
              <a
                key={link.source}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => setOpen(false)}
                className="verification-link"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 10px',
                  borderRadius: 6,
                  fontSize: 13,
                  color: 'var(--text-primary)',
                  textDecoration: 'none',
                  background: link.source === preferredSource ? 'var(--bg-hover)' : 'transparent',
                }}
              >
                <span>Open on {link.source}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                  <polyline points="15 3 21 3 21 9" />
                  <line x1="10" y1="14" x2="21" y2="3" />
                </svg>
              </a>
            ))}
          </div>

          <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid var(--border-color)', fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.4 }}>
            You are leaving Signal Desk. External websites may have different latency, session handling, or quote timing.
          </div>
        </div>
      )}
    </div>
  );
}
