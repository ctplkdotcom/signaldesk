export function formatPrice(price: number | null | undefined): string {
  if (price == null) return '--';
  return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '--';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

export function getDirectionColor(direction: string | null | undefined): string {
  switch (direction?.toLowerCase()) {
    case 'bullish': return 'var(--color-bullish)';
    case 'bearish': return 'var(--color-bearish)';
    default: return 'var(--color-neutral)';
  }
}

export function getHealthColor(status: string | null | undefined): string {
  switch (status?.toLowerCase()) {
    case 'healthy': return 'var(--color-bullish)';
    case 'warning': return 'var(--color-warning)';
    default: return 'var(--color-neutral)';
  }
}

export function scoreToLabel(score: number | null | undefined): { label: string; color: string } {
  if (score == null) return { label: 'No Signal', color: 'var(--color-neutral)' };
  if (score >= 70) return { label: 'Strong Bullish', color: 'var(--color-bullish)' };
  if (score >= 30) return { label: 'Bullish', color: 'var(--color-bullish)' };
  if (score > -30) return { label: 'Neutral', color: 'var(--color-neutral)' };
  if (score > -70) return { label: 'Bearish', color: 'var(--color-bearish)' };
  return { label: 'Strong Bearish', color: 'var(--color-bearish)' };
}
