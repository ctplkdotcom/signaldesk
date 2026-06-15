from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SessionType(str, Enum):
    PREMARKET = "premarket"
    REGULAR = "regular"
    AFTERHOURS = "afterhours"


class ProviderStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    RATE_LIMITED = "rate_limited"


@dataclass
class Quote:
    ticker: str
    timestamp_utc: datetime
    timestamp_et: datetime
    session: SessionType
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None
    bid: float | None = None
    ask: float | None = None
    trade_count: int | None = None
    provider: str = ""
    is_delayed: bool = False
    raw: dict | None = None


@dataclass
class PriceBar:
    ticker: str
    timestamp_utc: datetime
    timestamp_et: datetime
    session: SessionType
    open: float
    high: float
    low: float
    close: float
    volume: int
    trade_count: int | None = None
    bid: float | None = None
    ask: float | None = None
    provider: str = ""
    is_delayed: bool = False
    vwap: float | None = None
    raw: dict | None = None


@dataclass
class NewsArticle:
    provider_id: str
    provider: str
    title: str
    body: str | None = None
    url: str | None = None
    published_utc: datetime | None = None
    tickers: list[str] = field(default_factory=list)
    source: str | None = None
    event_type: str | None = None
    raw: dict | None = None


@dataclass
class ProviderHealth:
    provider: str
    status: ProviderStatus
    latency_ms: float | None = None
    message: str | None = None
    checked_at: datetime | None = None


class MarketDataProvider(ABC):
    @abstractmethod
    async def get_name(self) -> str: ...

    @abstractmethod
    async def check_health(self) -> ProviderHealth: ...

    @abstractmethod
    async def get_latest_quote(self, ticker: str) -> Quote | None: ...

    @abstractmethod
    async def get_bars(
        self,
        ticker: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timespan: str = "minute",
        limit: int = 1000,
    ) -> list[PriceBar]: ...

    @abstractmethod
    async def get_snapshot(self, ticker: str) -> Quote | None: ...


class NewsProvider(ABC):
    @abstractmethod
    async def get_name(self) -> str: ...

    @abstractmethod
    async def check_health(self) -> ProviderHealth: ...

    @abstractmethod
    async def get_news(
        self,
        tickers: list[str] | None = None,
        limit: int = 50,
        since: datetime | None = None,
    ) -> list[NewsArticle]: ...
