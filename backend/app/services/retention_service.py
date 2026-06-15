from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import delete

from app.database import async_session_factory
from app.models import (
    PriceBar,
    CleanPriceBar,
    QuoteSnapshot,
    NewsArticle,
    ScoredNews,
    Signal,
    DataHealth,
    ActivityLog,
)
from app.config import settings


class RetentionService:
    """Enforces data retention policy — deletes records older than retention_days."""

    async def cleanup(self) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.retention_days)
        results = {}

        tables = [
            ("price_bars", PriceBar, PriceBar.timestamp_utc),
            ("price_bars_1m_clean", CleanPriceBar, CleanPriceBar.timestamp_utc),
            ("quote_snapshots", QuoteSnapshot, QuoteSnapshot.timestamp_utc),
            ("news_articles", NewsArticle, NewsArticle.published_utc),
            ("scored_news", ScoredNews, ScoredNews.id),
            ("signals", Signal, Signal.generated_at),
            ("data_health", DataHealth, DataHealth.checked_at),
            ("activity_logs", ActivityLog, ActivityLog.timestamp),
        ]

        async with async_session_factory() as session:
            for name, model, ts_col in tables:
                try:
                    if name == "scored_news":
                        continue
                    stmt = delete(model).where(ts_col < cutoff)
                    result = await session.execute(stmt)
                    results[name] = result.rowcount or 0
                except Exception as e:
                    results[name] = f"error: {e}"
            await session.commit()

        return {"cutoff": cutoff.isoformat(), "deleted": results}
