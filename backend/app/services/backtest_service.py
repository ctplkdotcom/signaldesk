from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models import BacktestRun, BacktestResult, CleanPriceBar, Ticker, Methodology


class BacktestService:
    """Runs backtests using clean 1-minute bars from local database."""

    async def run_backtest(
        self,
        ticker: str,
        strategy: str = "momentum_5m",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        slippage: float = 0.001,
        fee: float = 0.001,
    ) -> dict:
        async with async_session_factory() as session:
            ticker_obj = (
                await session.execute(
                    select(Ticker).where(Ticker.ticker == ticker.upper())
                )
            ).scalar_one_or_none()

            if not ticker_obj:
                return {"error": "Ticker not found"}

            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=90)
            if not end_date:
                end_date = datetime.now(timezone.utc)

            bars = await self._get_bars(session, ticker_obj.id, start_date, end_date)

            if len(bars) < 20:
                return {
                    "error": f"Insufficient data: {len(bars)} bars (need at least 20)",
                }

            run = BacktestRun(
                ticker_id=ticker_obj.id,
                strategy_name=strategy,
                start_date=start_date,
                end_date=end_date,
                status="running",
                params={"slippage": slippage, "fee": fee},
            )
            session.add(run)
            await session.flush()

            try:
                if strategy == "momentum_5m":
                    result = await self._run_momentum_5m(bars, slippage, fee)
                elif strategy == "vwap_reversion":
                    result = await self._run_vwap_reversion(bars, slippage, fee)
                else:
                    return {"error": f"Unknown strategy: {strategy}"}

                bt_result = BacktestResult(
                    run_id=run.id,
                    **result,
                )
                session.add(bt_result)

                run.status = "completed"
                await session.commit()
                await session.refresh(bt_result)

                return {
                    "run_id": run.id,
                    "strategy": strategy,
                    "ticker": ticker.upper(),
                    "bars_used": len(bars),
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    **result,
                }

            except Exception as e:
                run.status = "failed"
                await session.commit()
                return {"error": str(e)}

    async def _get_bars(
        self, session: AsyncSession, ticker_id: int, start: datetime, end: datetime
    ) -> list:
        stmt = (
            select(CleanPriceBar)
            .where(
                and_(
                    CleanPriceBar.ticker_id == ticker_id,
                    CleanPriceBar.timestamp_utc >= start,
                    CleanPriceBar.timestamp_utc <= end,
                    CleanPriceBar.session == "REGULAR",
                )
            )
            .order_by(CleanPriceBar.timestamp_utc.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _run_momentum_5m(
        self, bars: list, slippage: float, fee: float
    ) -> dict:
        trades = []
        position = 0
        entry_price = 0.0
        entry_bar = 0

        for i in range(5, len(bars)):
            close_5m_ago = bars[i - 5].close
            current_close = bars[i].close
            momentum = (current_close - close_5m_ago) / close_5m_ago

            if position == 0 and momentum > 0.005:
                position = 1
                entry_price = current_close
                entry_bar = i
            elif position == 1 and momentum < -0.003:
                exit_price = current_close
                gross_return = (exit_price - entry_price) / entry_price
                net_return = gross_return - slippage - fee
                trades.append(
                    {
                        "entry_bar": entry_bar,
                        "exit_bar": i,
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "gross_return_pct": round(gross_return * 100, 2),
                        "net_return_pct": round(net_return * 100, 2),
                        "holding_bars": i - entry_bar,
                    }
                )
                position = 0

        if position != 0:
            exit_price = bars[-1].close
            gross_return = (exit_price - entry_price) / entry_price
            net_return = gross_return - slippage - fee
            trades.append(
                {
                    "entry_bar": entry_bar,
                    "exit_bar": len(bars) - 1,
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "gross_return_pct": round(gross_return * 100, 2),
                    "net_return_pct": round(net_return * 100, 2),
                    "holding_bars": len(bars) - 1 - entry_bar,
                }
            )

        return self._summarize_trades(trades)

    async def _run_vwap_reversion(
        self, bars: list, slippage: float, fee: float
    ) -> dict:
        trades = []
        position = 0
        entry_price = 0.0
        entry_bar = 0

        for i in range(10, len(bars)):
            recent = bars[i - 10 : i]
            vwap = sum(b.close * b.volume for b in recent if b.volume > 0) / max(
                sum(b.volume for b in recent if b.volume > 0), 1
            )
            current_close = bars[i].close
            deviation = (current_close - vwap) / vwap

            if position == 0 and deviation < -0.003:
                position = 1
                entry_price = current_close
                entry_bar = i
            elif position == 1 and deviation > 0.001:
                exit_price = current_close
                gross_return = (exit_price - entry_price) / entry_price
                net_return = gross_return - slippage - fee
                trades.append(
                    {
                        "entry_bar": entry_bar,
                        "exit_bar": i,
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "gross_return_pct": round(gross_return * 100, 2),
                        "net_return_pct": round(net_return * 100, 2),
                        "holding_bars": i - entry_bar,
                    }
                )
                position = 0

        return self._summarize_trades(trades)

    def _summarize_trades(self, trades: list) -> dict:
        if not trades:
            return {
                "total_return_pct": 0.0,
                "num_trades": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "max_drawdown_pct": 0.0,
                "avg_holding_bars": 0.0,
                "largest_loss": 0.0,
                "trade_log": [],
                "slippage_assumption": 0.001,
                "fee_assumption": 0.001,
            }

        wins = [t for t in trades if t["net_return_pct"] > 0]
        losses = [t for t in trades if t["net_return_pct"] <= 0]

        total_return = sum(t["net_return_pct"] for t in trades)
        win_rate = len(wins) / len(trades) if trades else 0
        avg_win = sum(t["net_return_pct"] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t["net_return_pct"] for t in losses) / len(losses) if losses else 0

        gross_wins = sum(t["gross_return_pct"] for t in wins)
        gross_losses = abs(sum(t["gross_return_pct"] for t in losses))
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float("inf")

        cumulative = 0
        peak = 0
        max_dd = 0
        for t in trades:
            cumulative += t["net_return_pct"]
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd

        avg_bars = sum(t["holding_bars"] for t in trades) / len(trades)
        largest_loss = min((t["net_return_pct"] for t in trades), default=0)

        return {
            "total_return_pct": round(total_return, 2),
            "num_trades": len(trades),
            "win_rate": round(win_rate, 4),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "avg_holding_bars": round(avg_bars, 1),
            "largest_loss": round(largest_loss, 2),
            "trade_log": trades,
            "slippage_assumption": 0.001,
            "fee_assumption": 0.001,
        }

    async def get_results(self, run_id: int) -> dict | None:
        async with async_session_factory() as session:
            run = (
                await session.execute(
                    select(BacktestRun).where(BacktestRun.id == run_id)
                )
            ).scalar_one_or_none()
            if not run:
                return None
            result = (
                await session.execute(
                    select(BacktestResult).where(BacktestResult.run_id == run.id)
                )
            ).scalar_one_or_none()
            return {
                "run_id": run.id,
                "strategy": run.strategy_name,
                "status": run.status,
                "result": result,
            }

    async def list_runs(self, limit: int = 20) -> list:
        async with async_session_factory() as session:
            stmt = (
                select(BacktestRun)
                .order_by(BacktestRun.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [
                {
                    "run_id": r.id,
                    "strategy": r.strategy_name,
                    "status": r.status,
                    "created_at": str(r.created_at),
                }
                for r in result.scalars().all()
            ]
