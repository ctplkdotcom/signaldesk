from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.data_health import DataHealth
from app.models.price_bar import PriceBar
from app.models.ticker import Ticker
from app.services.reference_data import ReferenceDataService
from app.utils.cache import cache


class DataHealthService:
    def __init__(self):
        self._ref_data = ReferenceDataService()

    async def check_ticker_health(self, ticker: str) -> DataHealth:
        t = await self._ref_data.get_ticker(ticker)
        if not t:
            return DataHealth(
                ticker_id=0, status="error",
                warning_type="Ticker Mapping Warning",
                message=f"Ticker {ticker} not found in reference data",
                checked_at=datetime.now(timezone.utc),
            )

        async with async_session_factory() as session:
            recent_bar = await session.execute(
                select(PriceBar)
                .where(PriceBar.ticker_id == t.id)
                .order_by(desc(PriceBar.timestamp_utc))
                .limit(1)
            )
            bar = recent_bar.scalar_one_or_none()

            bar_count = await session.execute(
                select(func.count(PriceBar.id))
                .where(PriceBar.ticker_id == t.id)
            )
            total_bars = bar_count.scalar() or 0

        now = datetime.now(timezone.utc)

        if not bar:
            status = "missing_data"
            warning_type = "Missing Data"
            message = f"No price data available for {ticker}"
        elif (now - bar.timestamp_utc) > timedelta(days=2):
            status = "stale"
            warning_type = "Stale Cache Warning"
            message = f"Last price data for {ticker} is from {bar.timestamp_utc.strftime('%Y-%m-%d %H:%M UTC')}"
        elif total_bars < 20:
            status = "low_liquidity"
            warning_type = "Low Liquidity"
            message = f"Only {total_bars} bars available for {ticker}, may affect signal quality"
        else:
            status = "healthy"
            warning_type = None
            message = "Data is current and sufficient"

        status_map = {
            "healthy": "healthy",
            "missing_data": "warning",
            "stale": "warning",
            "low_liquidity": "warning",
        }

        async with async_session_factory() as session:
            health = DataHealth(
                ticker_id=t.id,
                status=status_map.get(status, "warning"),
                warning_type=warning_type,
                message=message,
                checked_at=now,
                provider="polygon",
            )
            session.add(health)
            await session.commit()
            await session.refresh(health)
            await cache.delete(f"health:{ticker.upper()}")
            return health

    async def get_ticker_health(self, ticker: str) -> DataHealth | None:
        cache_key = f"health:{ticker.upper()}"
        cached = await cache.get(cache_key)
        if cached:
            return DataHealth(**cached) if isinstance(cached, dict) else cached

        t = await self._ref_data.get_ticker(ticker)
        if not t:
            return None

        async with async_session_factory() as session:
            result = await session.execute(
                select(DataHealth)
                .where(DataHealth.ticker_id == t.id)
                .order_by(desc(DataHealth.checked_at))
                .limit(1)
            )
            health = result.scalar_one_or_none()
            if health:
                await cache.set(cache_key, {
                    "id": health.id,
                    "ticker_id": health.ticker_id,
                    "status": health.status,
                    "warning_type": health.warning_type,
                    "message": health.message,
                    "checked_at": str(health.checked_at),
                    "provider": health.provider,
                }, ttl=120)
            return health

    async def get_all_health_warnings(self) -> list[dict]:
        async with async_session_factory() as session:
            subquery = (
                select(
                    DataHealth.ticker_id,
                    func.max(DataHealth.checked_at).label("max_checked")
                )
                .group_by(DataHealth.ticker_id)
                .subquery()
            )

            result = await session.execute(
                select(DataHealth)
                .join(subquery, (DataHealth.ticker_id == subquery.c.ticker_id) &
                      (DataHealth.checked_at == subquery.c.max_checked))
                .where(DataHealth.status != "healthy")
                .order_by(desc(DataHealth.checked_at))
            )

            records = result.scalars().all()
            output = []
            for r in records:
                ticker_obj = await self._ref_data.get_ticker_by_id(r.ticker_id)
                output.append({
                    "id": r.id,
                    "ticker": ticker_obj.ticker if ticker_obj else "unknown",
                    "status": r.status,
                    "warning_type": r.warning_type,
                    "message": r.message,
                    "checked_at": str(r.checked_at),
                })
            return output
