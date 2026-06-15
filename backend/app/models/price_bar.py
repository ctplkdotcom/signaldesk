from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Float, BigInteger, Boolean, DateTime, JSON, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PriceBar(Base):
    __tablename__ = "price_bars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), nullable=False, index=True)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    timestamp_et: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    session: Mapped[str] = mapped_column(String(20), nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    trade_count: Mapped[int | None] = mapped_column(Integer)
    bid: Mapped[float | None] = mapped_column(Float)
    ask: Mapped[float | None] = mapped_column(Float)
    vwap: Mapped[float | None] = mapped_column(Float)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    data_version: Mapped[int] = mapped_column(Integer, default=1)
    is_adjusted: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSON)

    ticker = relationship("Ticker", back_populates="price_bars")

    __table_args__ = (
        Index("ix_price_bars_ticker_ts", "ticker_id", "timestamp_utc"),
        Index("ix_price_bars_ticker_session_ts", "ticker_id", "session", "timestamp_utc"),
    )

    def __repr__(self) -> str:
        return f"<PriceBar {self.ticker_id} @ {self.timestamp_et} [{self.session}]>"
