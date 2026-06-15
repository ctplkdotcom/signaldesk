from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import String, Boolean, Date, DateTime, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Ticker(Base):
    __tablename__ = "tickers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    asset_type: Mapped[str | None] = mapped_column(String(50))
    exchange: Mapped[str | None] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_traded: Mapped[date | None] = mapped_column(Date)
    last_traded: Mapped[date | None] = mapped_column(Date)
    provider_mappings: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    price_bars = relationship("PriceBar", back_populates="ticker", lazy="dynamic")
    news_articles = relationship("NewsArticle", back_populates="ticker", lazy="dynamic")
    signals = relationship("Signal", back_populates="ticker", lazy="dynamic")
    data_health_records = relationship("DataHealth", back_populates="ticker", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Ticker {self.ticker}>"
