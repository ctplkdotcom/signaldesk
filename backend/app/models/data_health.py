from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DataHealth(Base):
    __tablename__ = "data_health"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="healthy")
    warning_type: Mapped[str | None] = mapped_column(String(100))
    message: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    provider: Mapped[str | None] = mapped_column(String(50))

    ticker = relationship("Ticker", back_populates="data_health_records")

    def __repr__(self) -> str:
        return f"<DataHealth {self.ticker_id} status={self.status}>"
