from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, desc

from app.database import async_session_factory
from app.models.news_article import NewsArticle
from app.models.scored_news import ScoredNews
from app.services.reference_data import ReferenceDataService
from app.services.scoring import NewsScoringEngine
from app.utils.cache import cache


class NewsService:
    def __init__(self):
        self._ref_data = ReferenceDataService()
        self._scoring = NewsScoringEngine()

    async def store_article(
        self,
        title: str,
        body: str | None = None,
        url: str | None = None,
        source: str | None = None,
        event_type: str | None = None,
        published_utc: datetime | None = None,
        ticker: str | None = None,
    ) -> dict[str, Any]:
        ticker_id = None
        if ticker:
            t = await self._ref_data.get_or_create_ticker(ticker.upper())
            ticker_id = t.id

        async with async_session_factory() as session:
            article = NewsArticle(
                ticker_id=ticker_id,
                provider_id=f"manual_{datetime.now(timezone.utc).timestamp()}",
                provider="manual",
                title=title,
                body=body,
                url=url,
                published_utc=published_utc or datetime.now(timezone.utc),
                source=source,
                event_type=event_type,
            )
            session.add(article)
            await session.commit()
            await session.refresh(article)

        score = await self._scoring.score_article(
            article_id=article.id,
            title=article.title,
            body=article.body,
            event_type=article.event_type,
            source=article.source,
            published_utc=article.published_utc,
        )

        await cache.clear_pattern("news:*")
        return {
            "id": article.id,
            "title": article.title,
            "score": score["final_score"],
            "label": score["label"],
            "explanation": score["explanation"],
        }

    async def get_news(
        self,
        ticker: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        async with async_session_factory() as session:
            query = select(NewsArticle).join(ScoredNews, isouter=True)
            if ticker:
                query = query.where(NewsArticle.ticker.has(ticker=ticker.upper()))
            query = query.order_by(desc(NewsArticle.published_utc)).limit(limit).offset(offset)
            result = await session.execute(query)
            articles = result.scalars().all()

            output = []
            for a in articles:
                s = a.scored_news
                output.append({
                    "id": a.id,
                    "title": a.title,
                    "body": a.body,
                    "url": a.url,
                    "published_utc": str(a.published_utc),
                    "source": a.source or "manual",
                    "event_type": a.event_type,
                    "score": s.final_score if s else None,
                    "label": s.label if s else None,
                    "sentiment": s.sentiment_score if s else None,
                    "explanation": s.explanation if s else None,
                })
            return output

    async def get_article(self, article_id: int) -> dict[str, Any] | None:
        async with async_session_factory() as session:
            result = await session.execute(
                select(NewsArticle).where(NewsArticle.id == article_id)
            )
            a = result.scalar_one_or_none()
            if not a:
                return None
            s = a.scored_news
            return {
                "id": a.id,
                "title": a.title,
                "body": a.body,
                "url": a.url,
                "published_utc": str(a.published_utc),
                "source": a.source,
                "event_type": a.event_type,
                "tickers": a.tickers,
                "scored_news": {
                    "final_score": s.final_score,
                    "label": s.label,
                    "sentiment_score": s.sentiment_score,
                    "event_score": s.event_score,
                    "source_score": s.source_score,
                    "recency_score": s.recency_score,
                    "components": s.components,
                    "explanation": s.explanation,
                } if s else None,
            }
