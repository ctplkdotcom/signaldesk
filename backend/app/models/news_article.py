from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, JSON, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_id: Mapped[int | None] = mapped_column(ForeignKey("tickers.id"), index=True)
    provider_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    published_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    tickers: Mapped[list | None] = mapped_column(JSON)
    source: Mapped[str | None] = mapped_column(String(255))
    event_type: Mapped[str | None] = mapped_column(String(100))
    raw_payload: Mapped[dict | None] = mapped_column(JSON)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticker = relationship("Ticker", back_populates="news_articles")
    scored_news = relationship("ScoredNews", back_populates="news_article", uselist=False)

    __table_args__ = (
        UniqueConstraint("provider", "provider_id", name="uq_news_provider_ref"),
    )

    def __repr__(self) -> str:
        return f"<NewsArticle #{self.id} {self.title[:50]}>"
