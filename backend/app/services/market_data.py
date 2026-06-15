from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, desc

from app.database import async_session_factory
from app.models.price_bar import PriceBar
from app.providers.base import MarketDataProvider, PriceBar as ProviderPriceBar
from app.providers.polygon import PolygonProvider
from app.services.reference_data import ReferenceDataService
from app.utils.cache import cache
from app.utils.time import to_utc, to_et
from app.config import settings


class MarketDataService:
    def __init__(self):
        self._provider: MarketDataProvider | None = None
        self._ref_data = ReferenceDataService()

    async def _get_provider(self) -> MarketDataProvider:
        if self._provider is None:
            self._provider = PolygonProvider()
        return self._provider

    async def get_latest_quote(self, ticker: str) -> Any | None:
        cache_key = f"quote:{ticker.upper()}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        provider = await self._get_provider()
        try:
            quote = await provider.get_latest_quote(ticker)
            if quote:
                quote_dict = {
                    "ticker": quote.ticker,
                    "price": quote.close,
                    "open": quote.open,
                    "high": quote.high,
                    "low": quote.low,
                    "volume": quote.volume,
                    "bid": quote.bid,
                    "ask": quote.ask,
                    "session": quote.session.value if hasattr(quote.session, "value") else str(quote.session),
                    "timestamp_utc": str(quote.timestamp_utc),
                    "timestamp_et": str(quote.timestamp_et),
                    "provider": quote.provider,
                }
                await cache.set(cache_key, quote_dict, ttl=settings.cache_ttl_price)
                return quote_dict
        except Exception:
            pass
        return None

    async def get_and_store_bars(
        self,
        ticker: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timespan: str = "minute",
        limit: int = 1000,
    ) -> list[PriceBar]:
        provider = await self._get_provider()
        provider_bars = await provider.get_bars(ticker, start, end, timespan, limit)
        if not provider_bars:
            return []

        t = await self._ref_data.get_or_create_ticker(ticker)
        async with async_session_factory() as session:
            existing = await session.execute(
                select(PriceBar.timestamp_utc)
                .where(PriceBar.ticker_id == t.id)
                .order_by(desc(PriceBar.timestamp_utc))
                .limit(1)
            )
            last_ts = existing.scalar_one_or_none()

            count = 0
            for bar in provider_bars:
                if last_ts and bar.timestamp_utc <= last_ts:
                    continue
                pb = PriceBar(
                    ticker_id=t.id,
                    timestamp_utc=to_utc(bar.timestamp_utc),
                    timestamp_et=to_et(bar.timestamp_et),
                    session=bar.session.value if hasattr(bar.session, "value") else str(bar.session),
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume or 0,
                    trade_count=bar.trade_count,
                    provider=bar.provider or "polygon",
                    raw_payload=bar.raw,
                )
                session.add(pb)
                count += 1

            if count > 0:
                await session.commit()
                await cache.clear_pattern(f"bars:{ticker.upper()}:*")
                await cache.clear_pattern(f"quote:{ticker.upper()}*")

        return await self._get_stored_bars(t, start, end, limit)

    async def _get_stored_bars(
        self,
        ticker_or_id: Any,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 1000,
    ) -> list[PriceBar]:
        ticker_id = ticker_or_id.id if hasattr(ticker_or_id, "id") else ticker_or_id
        async with async_session_factory() as session:
            query = select(PriceBar).where(PriceBar.ticker_id == ticker_id)
            if start:
                query = query.where(PriceBar.timestamp_utc >= to_utc(start))
            if end:
                query = query.where(PriceBar.timestamp_utc <= to_utc(end))
            query = query.order_by(PriceBar.timestamp_utc.desc()).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_bars(
        self,
        ticker: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timespan: str = "minute",
        limit: int = 1000,
    ) -> list[PriceBar]:
        t = await self._ref_data.get_ticker(ticker)
        if not t:
            return []
        return await self._get_stored_bars(t, start, end, limit)
