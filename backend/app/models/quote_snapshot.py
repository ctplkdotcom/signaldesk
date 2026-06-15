from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Float, BigInteger, DateTime, JSON, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class QuoteSnapshot(Base):
    __tablename__ = "quote_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), nullable=False, index=True)
    timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    bid: Mapped[float | None] = mapped_column(Float)
    ask: Mapped[float | None] = mapped_column(Float)
    bid_size: Mapped[int | None] = mapped_column(Integer)
    ask_size: Mapped[int | None] = mapped_column(Integer)
    volume: Mapped[int] = mapped_column(BigInteger, default=0)
    session: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSON)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    ticker = relationship("Ticker")

    __table_args__ = (
        Index("ix_quote_snapshots_ticker_ts", "ticker_id", "timestamp_utc"),
    )

    def __repr__(self) -> str:
        return f"<QuoteSnapshot #{self.id} ticker={self.ticker_id} price={self.price}>"
