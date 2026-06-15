from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WatchlistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker_id: int
    ticker_symbol: str | None = None
    ticker_name: str | None = None
    added_at: datetime

    last_price: float | None = None
    price_change: float | None = None
    price_change_pct: float | None = None
    session: str | None = None
    health_status: str | None = None
    signal_direction: str | None = None
    signal_strength: float | None = None


class WatchlistSummary(BaseModel):
    items: list[WatchlistItemRead]
    count: int
    last_updated: datetime | None = None


class DashboardSummary(BaseModel):
    watchlist: WatchlistSummary
    market_hours: str | None = None
    total_signals: int = 0
    total_alerts: int = 0
    system_health: str = "healthy"
    last_updated: datetime | None = None
