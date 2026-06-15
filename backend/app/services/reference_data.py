from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.ticker import Ticker
from app.models.watchlist import WatchlistItem
from app.models.data_health import DataHealth
from app.utils.cache import cache
from app.config import settings


class ReferenceDataService:
    async def get_or_create_ticker(
        self,
        ticker: str,
        name: str | None = None,
        asset_type: str | None = "stock",
        exchange: str | None = "NASDAQ",
    ) -> Ticker:
        async with async_session_factory() as session:
            result = await session.execute(select(Ticker).where(Ticker.ticker == ticker.upper()))
            t = result.scalar_one_or_none()
            if t:
                return t
            t = Ticker(
                ticker=ticker.upper(),
                name=name or ticker.upper(),
                asset_type=asset_type,
                exchange=exchange,
                is_active=True,
            )
            session.add(t)
            await session.commit()
            await session.refresh(t)
            await cache.delete(f"ticker:{ticker.upper()}")
            return t

    async def get_ticker(self, ticker: str) -> Ticker | None:
        cache_key = f"ticker:{ticker.upper()}"
        cached = await cache.get(cache_key)
        if cached:
            return Ticker(**cached) if isinstance(cached, dict) else cached

        async with async_session_factory() as session:
            result = await session.execute(select(Ticker).where(Ticker.ticker == ticker.upper()))
            t = result.scalar_one_or_none()
            if t:
                await cache.set(cache_key, {
                    "id": t.id,
                    "ticker": t.ticker,
                    "name": t.name,
                    "asset_type": t.asset_type,
                    "exchange": t.exchange,
                    "currency": t.currency,
                    "is_active": t.is_active,
                    "first_traded": str(t.first_traded) if t.first_traded else None,
                    "last_traded": str(t.last_traded) if t.last_traded else None,
                }, ttl=settings.cache_ttl_ticker)
            return t

    async def get_ticker_by_id(self, ticker_id: int) -> Ticker | None:
        async with async_session_factory() as session:
            result = await session.execute(select(Ticker).where(Ticker.id == ticker_id))
            return result.scalar_one_or_none()

    async def list_tickers(self, active_only: bool = True) -> list[Ticker]:
        async with async_session_factory() as session:
            query = select(Ticker)
            if active_only:
                query = query.where(Ticker.is_active == True)
            query = query.order_by(Ticker.ticker)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def add_to_watchlist(self, ticker: str) -> WatchlistItem | None:
        t = await self.get_ticker(ticker)
        if not t:
            return None
        async with async_session_factory() as session:
            existing = await session.execute(
                select(WatchlistItem).where(WatchlistItem.ticker_id == t.id)
            )
            if existing.scalar_one_or_none():
                return None
            item = WatchlistItem(ticker_id=t.id)
            session.add(item)
            await session.commit()
            await session.refresh(item)
            await cache.delete("watchlist")
            return item

    async def remove_from_watchlist(self, ticker: str) -> bool:
        t = await self.get_ticker(ticker)
        if not t:
            return False
        async with async_session_factory() as session:
            result = await session.execute(
                select(WatchlistItem).where(WatchlistItem.ticker_id == t.id)
            )
            item = result.scalar_one_or_none()
            if not item:
                return False
            await session.delete(item)
            await session.commit()
            await cache.delete("watchlist")
            return True

    async def get_watchlist(self) -> list[WatchlistItem]:
        cached = await cache.get("watchlist")
        if cached:
            return [WatchlistItem(**i) if isinstance(i, dict) else i for i in cached]

        async with async_session_factory() as session:
            result = await session.execute(
                select(WatchlistItem).order_by(WatchlistItem.added_at)
            )
            items = list(result.scalars().all())
            await cache.set("watchlist", [
                {"id": i.id, "ticker_id": i.ticker_id, "added_at": str(i.added_at)}
                for i in items
            ], ttl=300)
            return items
