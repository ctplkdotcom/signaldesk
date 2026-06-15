from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    String, Integer, Float, Text, DateTime, JSON, BigInteger, ForeignKey, func, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    params: Mapped[dict | None] = mapped_column(JSON)
    data_health_warning: Mapped[bool] = mapped_column(default=False)

    results = relationship("BacktestResult", back_populates="run", uselist=False)

    def __repr__(self) -> str:
        return f"<BacktestRun #{self.id} {self.strategy_name} ({self.status})>"


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("backtest_runs.id"), nullable=False, unique=True
    )
    total_return_pct: Mapped[float] = mapped_column(Float)
    num_trades: Mapped[int] = mapped_column(Integer, default=0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_win: Mapped[float] = mapped_column(Float, default=0.0)
    avg_loss: Mapped[float] = mapped_column(Float, default=0.0)
    profit_factor: Mapped[float] = mapped_column(Float, default=0.0)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, default=0.0)
    avg_holding_bars: Mapped[float] = mapped_column(Float, default=0.0)
    largest_loss: Mapped[float] = mapped_column(Float, default=0.0)
    slippage_assumption: Mapped[float] = mapped_column(Float, default=0.001)
    fee_assumption: Mapped[float] = mapped_column(Float, default=0.001)
    trade_log: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    run = relationship("BacktestRun", back_populates="results")

    __table_args__ = (Index("ix_backtest_results_run", "run_id"),)

    def __repr__(self) -> str:
        return f"<BacktestResult #{self.id} run={self.run_id} return={self.total_return_pct:.2f}%>"
