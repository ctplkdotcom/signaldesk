from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BarQuery(BaseModel):
    ticker: str
    start: datetime | None = None
    end: datetime | None = None
    session: str | None = None
    limit: int = 1000
    adjusted: bool = False


class PriceBarRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker_id: int
    timestamp_utc: datetime
    timestamp_et: datetime
    session: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    trade_count: int | None
    bid: float | None
    ask: float | None
    provider: str
    is_adjusted: bool


class PriceBarList(BaseModel):
    items: list[PriceBarRead]
    ticker: str
    count: int
