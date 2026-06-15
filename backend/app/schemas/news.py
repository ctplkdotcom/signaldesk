from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ScoredNewsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    news_id: int
    sentiment_score: float
    event_score: float
    source_score: float
    recency_score: float
    final_score: float
    components: dict | None
    explanation: str | None
    label: str | None
    version: str


class NewsArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker_id: int | None
    provider: str
    title: str
    body: str | None
    url: str | None
    published_utc: datetime
    tickers: list[str] | None
    source: str | None
    event_type: str | None
    scored_news: ScoredNewsRead | None


class NewsArticleList(BaseModel):
    items: list[NewsArticleRead]
    total: int
