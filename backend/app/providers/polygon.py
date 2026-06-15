from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
import pytz

from app.config import settings
from app.providers.base import (
    MarketDataProvider,
    PriceBar,
    Quote,
    ProviderHealth,
    ProviderStatus,
    SessionType,
)
from app.utils.time import get_et_now, classify_session, to_utc, to_et


class PolygonProvider(MarketDataProvider):
    BASE_URL = "https://api.polygon.io"

    def __init__(self):
        self.api_key = settings.polygon_api_key
        self._client: httpx.AsyncClient | None = None
        self._et_tz = pytz.timezone("US/Eastern")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                params={"apiKey": self.api_key},
                timeout=settings.request_timeout,
            )
        return self._client

    async def get_name(self) -> str:
        return "polygon"

    async def check_health(self) -> ProviderHealth:
        try:
            client = await self._get_client()
            start = asyncio.get_event_loop().time()
            resp = await client.get("/v2/reference/markets")
            latency = (asyncio.get_event_loop().time() - start) * 1000
            if resp.status_code == 200:
                return ProviderHealth(
                    provider="polygon",
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency,
                    checked_at=datetime.now(timezone.utc),
                )
            return ProviderHealth(
                provider="polygon",
                status=ProviderStatus.DEGRADED,
                message=f"HTTP {resp.status_code}",
                checked_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            return ProviderHealth(
                provider="polygon",
                status=ProviderStatus.DOWN,
                message=str(e),
                checked_at=datetime.now(timezone.utc),
            )

    async def get_latest_quote(self, ticker: str) -> Quote | None:
        client = await self._get_client()
        try:
            resp = await client.get(f"/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}")
            if resp.status_code != 200:
                return None
            data = resp.json()
            ticker_data = data.get("ticker", {})
            last = ticker_data.get("prevDay", {})
            session_data = ticker_data.get("session", {})
            now_et = get_et_now()
            session = classify_session(now_et)

            quote_data = ticker_data.get("lastQuote", {}) or {}
            trade_data = ticker_data.get("lastTrade", {}) or {}

            return Quote(
                ticker=ticker.upper(),
                timestamp_utc=to_utc(now_et),
                timestamp_et=now_et,
                session=session,
                open=last.get("o"),
                high=last.get("h"),
                low=last.get("l"),
                close=last.get("c"),
                volume=session_data.get("volume"),
                bid=quote_data.get("p"),
                ask=quote_data.get("P"),
                trade_count=session_data.get("volume"),
                provider="polygon",
                is_delayed=False,
                raw=data,
            )
        except httpx.TimeoutException:
            return None

    async def get_snapshot(self, ticker: str) -> Quote | None:
        return await self.get_latest_quote(ticker)

    async def get_bars(
        self,
        ticker: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timespan: str = "minute",
        limit: int = 1000,
    ) -> list[PriceBar]:
        client = await self._get_client()
        end = end or datetime.now(timezone.utc)
        start = start or (end - timedelta(days=7))

        bars: list[PriceBar] = []
        url = f"/v2/aggs/ticker/{ticker}/range/1/{timespan}/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"

        try:
            while url:
                resp = await client.get(url)
                if resp.status_code != 200:
                    break

                data = resp.json()
                results = data.get("results", [])

                for r in results:
                    ts = datetime.fromtimestamp(r["t"] / 1000, tz=timezone.utc)
                    ts_et = to_et(ts)
                    session = classify_session(ts_et)

                    bars.append(PriceBar(
                        ticker=ticker.upper(),
                        timestamp_utc=ts,
                        timestamp_et=ts_et,
                        session=session,
                        open=float(r["o"]),
                        high=float(r["h"]),
                        low=float(r["l"]),
                        close=float(r["c"]),
                        volume=int(r.get("v", 0)),
                        vwap=float(r["vw"]) if "vw" in r else None,
                        trade_count=int(r.get("n", 0)) if "n" in r else None,
                        provider="polygon",
                        raw=r,
                    ))

                url = data.get("next_url")
                if url:
                    url = f"{url}&apiKey={self.api_key}"

        except httpx.TimeoutException:
            pass

        return bars

    async def close(self):
        if self._client:
            await self._client.aclose()
