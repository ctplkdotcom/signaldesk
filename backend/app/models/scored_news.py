from __future__ import annotations

from sqlalchemy import Integer, Float, Text, String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScoredNews(Base):
    __tablename__ = "scored_news"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    news_id: Mapped[int] = mapped_column(ForeignKey("news_articles.id"), unique=True, nullable=False)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    event_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    components: Mapped[dict | None] = mapped_column(JSON)
    explanation: Mapped[str | None] = mapped_column(Text)
    label: Mapped[str | None] = mapped_column(String(50))
    version: Mapped[str] = mapped_column(String(20), default="1.0")

    news_article = relationship("NewsArticle", back_populates="scored_news")

    def __repr__(self) -> str:
        return f"<ScoredNews #{self.id} score={self.final_score:.1f} label={self.label}>"
