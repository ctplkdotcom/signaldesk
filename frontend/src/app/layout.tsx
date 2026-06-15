import type { Metadata } from 'next';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: 'Signal Desk',
  description: 'Stock analysis, news scoring, and signal generation for US equities',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Nav />
        <main style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 24px 48px' }}>
          {children}
        </main>
      </body>
    </html>
  );
}

function Nav() {
  return (
    <nav style={{
      height: 56,
      borderBottom: '1px solid var(--border-color)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 24px',
      background: 'var(--bg-secondary)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <a href="/" style={{
        fontSize: 20,
        fontWeight: 700,
        color: 'var(--text-primary)',
        letterSpacing: '-0.02em',
        textDecoration: 'none',
      }}>
        Signal Desk
      </a>
      <div style={{ display: 'flex', gap: 4, marginLeft: 32, overflowX: 'auto' }}>
        <NavLink href="/dashboard">Dashboard</NavLink>
        <NavLink href="/watchlist">Watchlist</NavLink>
        <NavLink href="/analysis">Analysis</NavLink>
        <NavLink href="/news">News</NavLink>
        <NavLink href="/health">Data Health</NavLink>
        <NavLink href="/backtest">Backtest</NavLink>
        <NavLink href="/activity-log">Activity Log</NavLink>
        <NavLink href="/methodologies">Methods</NavLink>
      </div>
    </nav>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      className="nav-link"
      style={{
        padding: '6px 12px',
        borderRadius: 8,
        color: 'var(--text-secondary)',
        fontSize: 14,
        fontWeight: 500,
        textDecoration: 'none',
        transition: 'all 0.15s',
      }}
    >
      {children}
    </a>
  );
}
