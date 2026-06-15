from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, JSON, BigInteger, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ticker: Mapped[str | None] = mapped_column(String(20), index=True)
    message: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict | None] = mapped_column(JSON)
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        Index("ix_activity_logs_action_time", "action", "timestamp"),
        Index("ix_activity_logs_ticker_time", "ticker", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<ActivityLog #{self.id} {self.action} [{self.level}]>"
