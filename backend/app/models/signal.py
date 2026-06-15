from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    strategy_type: Mapped[str] = mapped_column(String(100), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    strength: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    explanation: Mapped[str | None] = mapped_column(Text)
    data_sources: Mapped[dict | None] = mapped_column(JSON)

    ticker = relationship("Ticker", back_populates="signals")

    def __repr__(self) -> str:
        return f"<Signal #{self.id} {self.ticker_id} {self.direction} [{self.strategy_type}]>"
