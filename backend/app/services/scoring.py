from __future__ import annotations

import math
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.news_article import NewsArticle
from app.models.scored_news import ScoredNews
from app.utils.cache import cache


class ScoreLabel(str, Enum):
    STRONG_BULLISH = "Strong Bullish"
    BULLISH = "Bullish"
    NEUTRAL = "Neutral"
    BEARISH = "Bearish"
    STRONG_BEARISH = "Strong Bearish"


SCORE_BANDS: list[tuple[float, float, ScoreLabel]] = [
    (70, 100, ScoreLabel.STRONG_BULLISH),
    (30, 69, ScoreLabel.BULLISH),
    (-29, 29, ScoreLabel.NEUTRAL),
    (-69, -30, ScoreLabel.BEARISH),
    (-100, -70, ScoreLabel.STRONG_BEARISH),
]

FINANCIAL_SENTIMENT_LEXICON: dict[str, float] = {
    # Strong positive
    "beat": 0.8, "surge": 0.9, "soar": 0.9, "rally": 0.8, "boom": 0.9,
    "growth": 0.7, "profit": 0.8, "upgrade": 0.7, "outperform": 0.8,
    "record": 0.7, "bullish": 0.9, "positive": 0.6, "gain": 0.6,
    "strong": 0.6, "exceed": 0.7, "raise": 0.6, "upbeat": 0.7,
    "recovery": 0.6, "expansion": 0.6, "dividend": 0.5, "buyback": 0.7,
    "innovation": 0.5, "partnership": 0.5, "launch": 0.4,
    # Moderate positive
    "rise": 0.4, "increase": 0.4, "higher": 0.4, "improve": 0.5,
    "optimistic": 0.6, "confidence": 0.5, "opportunity": 0.4,
    "momentum": 0.5, "uptrend": 0.6, "breakthrough": 0.6,
    # Negative
    "miss": -0.7, "decline": -0.6, "drop": -0.7, "fall": -0.6,
    "loss": -0.7, "downgrade": -0.7, "sell-off": -0.8, "bearish": -0.8,
    "negative": -0.6, "weak": -0.5, "cut": -0.5, "reduce": -0.4,
    "slump": -0.7, "plunge": -0.8, "crash": -0.9, "recession": -0.8,
    "volatile": -0.3, "uncertainty": -0.4, "risk": -0.3, "debt": -0.5,
    "lawsuit": -0.7, "investigation": -0.7, "fine": -0.6, "penalty": -0.6,
    # Strong negative
    "bankrupt": -0.9, "fraud": -0.9, "scandal": -0.9, "delist": -0.9,
    "default": -0.8, "downturn": -0.7, "layoff": -0.5, "restructuring": -0.4,
}

EVENT_TYPE_SCORES: dict[str, float] = {
    "earnings": 0.6, "earnings_beat": 0.9, "earnings_miss": -0.9,
    "guidance": 0.5, "guidance_up": 0.8, "guidance_down": -0.8,
    "analyst_upgrade": 0.7, "analyst_downgrade": -0.7,
    "merger": 0.4, "acquisition": 0.4, "divestiture": 0.3,
    "stock_split": 0.2, "dividend": 0.5, "buyback": 0.6,
    "sec_filing": 0.1, "ipo": 0.3, "secondary_offering": -0.3,
    "legal": -0.6, "regulatory": -0.4, "product_launch": 0.4,
    "partnership": 0.4, "expansion": 0.5, "restructuring": -0.3,
    "layoff": -0.4, "ceo_change": 0.2, "board_change": 0.1,
    "macro": 0.1, "sector": 0.2, "market": 0.1,
    "general": 0.0,
}

SOURCE_RELIABILITY: dict[str, float] = {
    "benzinga": 0.8, "reuters": 0.9, "bloomberg": 0.9, "cnbc": 0.8,
    "marketwatch": 0.7, "seeking_alpha": 0.5, "yahoo_finance": 0.6,
    "pr_newswire": 0.5, "business_wire": 0.6, "sec": 0.95,
    "company": 0.4, "unknown": 0.3,
}

EVENT_TYPE_MAP: dict[str, str] = {
    "earnings": "earnings",
    "earnings beat": "earnings_beat",
    "earnings miss": "earnings_miss",
    "guidance": "guidance",
    "guidance raised": "guidance_up",
    "guidance lowered": "guidance_down",
    "upgrade": "analyst_upgrade",
    "downgrade": "analyst_downgrade",
    "merger": "merger",
    "acquisition": "acquisition",
    "dividend": "dividend",
    "buyback": "buyback",
    "stock split": "stock_split",
    "ipo": "ipo",
    "legal": "legal",
    "regulatory": "regulatory",
    "product": "product_launch",
    "partnership": "partnership",
    "layoff": "layoff",
    "ceo": "ceo_change",
    "macro": "macro",
    "sector": "sector",
    "market": "market",
}


class NewsScoringEngine:
    def __init__(
        self,
        sentiment_weight: float = 0.40,
        event_weight: float = 0.30,
        source_weight: float = 0.20,
        recency_weight: float = 0.10,
        recency_lambda: float = 0.1,
    ):
        self.sentiment_weight = sentiment_weight
        self.event_weight = event_weight
        self.source_weight = source_weight
        self.recency_weight = recency_weight
        self.recency_lambda = recency_lambda

    def _compute_sentiment(self, title: str, body: str | None = None) -> float:
        text = f"{title} {body or ''}".lower()
        scores = []
        for word, score in FINANCIAL_SENTIMENT_LEXICON.items():
            if word in text:
                scores.append(score)
        if not scores:
            return 0.0
        return sum(scores) / len(scores) * 100

    def _map_event_type(self, event_type: str | None) -> str:
        if not event_type:
            return "general"
        et = event_type.lower().strip()
        return EVENT_TYPE_MAP.get(et, "general")

    def _compute_event_score(self, event_type: str | None) -> float:
        if not event_type:
            return 0.0
        et = event_type.lower().strip()
        if et in EVENT_TYPE_SCORES:
            return EVENT_TYPE_SCORES[et] * 100
        mapped = self._map_event_type(event_type)
        return EVENT_TYPE_SCORES.get(mapped, 0.0) * 100

    def _compute_source_score(self, source: str | None) -> float:
        if not source:
            return SOURCE_RELIABILITY.get("unknown", 0.3) * 100
        s = source.lower().replace(" ", "_")
        return SOURCE_RELIABILITY.get(s, SOURCE_RELIABILITY["unknown"]) * 100

    def _compute_recency(self, published_utc: datetime | None) -> float:
        if not published_utc:
            return 0.0
        now = datetime.now(timezone.utc)
        hours_ago = (now - published_utc).total_seconds() / 3600
        decay = math.exp(-self.recency_lambda * hours_ago)
        return max(0, min(100, decay * 100))

    def _compute_label(self, score: float) -> ScoreLabel:
        for low, high, label in SCORE_BANDS:
            if low <= score <= high:
                return label
        return ScoreLabel.NEUTRAL

    def _generate_explanation(
        self,
        sentiment: float,
        event: float,
        source: float,
        recency: float,
        final: float,
        components: dict,
    ) -> str:
        parts = []
        if abs(sentiment) > 30:
            direction = "positive" if sentiment > 0 else "negative"
            parts.append(f"Sentiment is {direction} ({sentiment:.0f})")
        if abs(event) > 20:
            direction = "positive" if event > 0 else "negative"
            parts.append(f"Event type impact is {direction} ({event:.0f})")
        if source > 50:
            parts.append(f"Source reliability is good ({source:.0f})")
        else:
            parts.append(f"Source reliability is low ({source:.0f})")
        if recency > 50:
            parts.append(f"News is recent ({recency:.0f})")
        else:
            parts.append(f"News is older ({recency:.0f})")
        return " | ".join(parts) if parts else "No significant factors"

    async def score_article(
        self,
        article_id: int,
        title: str,
        body: str | None = None,
        event_type: str | None = None,
        source: str | None = None,
        published_utc: datetime | None = None,
    ) -> dict[str, Any]:
        sentiment_raw = self._compute_sentiment(title, body)
        sentiment_score = max(-100, min(100, sentiment_raw))

        event_score = self._compute_event_score(event_type)
        source_score = self._compute_source_score(source)
        recency_score = self._compute_recency(published_utc)

        final = (
            self.sentiment_weight * sentiment_score
            + self.event_weight * event_score
            + self.source_weight * source_score
            + self.recency_weight * recency_score
        )
        final = max(-100, min(100, final))

        components = {
            "sentiment": sentiment_score,
            "event": event_score,
            "source": source_score,
            "recency": recency_score,
            "weights": {
                "sentiment_weight": self.sentiment_weight,
                "event_weight": self.event_weight,
                "source_weight": self.source_weight,
                "recency_weight": self.recency_weight,
            },
        }

        label = self._compute_label(final)
        explanation = self._generate_explanation(
            sentiment_score, event_score, source_score, recency_score, final, components
        )

        async with async_session_factory() as session:
            existing = await session.execute(
                select(ScoredNews).where(ScoredNews.news_id == article_id)
            )
            scored = existing.scalar_one_or_none()

            if scored:
                scored.sentiment_score = sentiment_score
                scored.event_score = event_score
                scored.source_score = source_score
                scored.recency_score = recency_score
                scored.final_score = final
                scored.components = components
                scored.explanation = explanation
                scored.label = label.value
                scored.version = "1.0"
            else:
                scored = ScoredNews(
                    news_id=article_id,
                    sentiment_score=sentiment_score,
                    event_score=event_score,
                    source_score=source_score,
                    recency_score=recency_score,
                    final_score=final,
                    components=components,
                    explanation=explanation,
                    label=label.value,
                    version="1.0",
                )
                session.add(scored)

            await session.commit()
            await cache.clear_pattern(f"news:*")

        return {
            "article_id": article_id,
            "final_score": final,
            "label": label.value,
            "components": components,
            "explanation": explanation,
        }

    async def score_all_unscored(self):
        async with async_session_factory() as session:
            result = await session.execute(
                select(NewsArticle)
                .outerjoin(ScoredNews)
                .where(ScoredNews.id.is_(None))
                .order_by(NewsArticle.published_utc.desc())
                .limit(200)
            )
            articles = result.scalars().all()

        for article in articles:
            await self.score_article(
                article_id=article.id,
                title=article.title,
                body=article.body,
                event_type=article.event_type,
                source=article.source,
                published_utc=article.published_utc,
            )
