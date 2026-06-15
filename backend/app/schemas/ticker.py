from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class TickerCreate(BaseModel):
    ticker: str
    name: str | None = None
    asset_type: str | None = None
    exchange: str | None = None
    currency: str = "USD"
    is_active: bool = True
    first_traded: date | None = None
    last_traded: date | None = None
    provider_mappings: dict | None = None


class TickerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    name: str | None
    asset_type: str | None
    exchange: str | None
    currency: str
    is_active: bool
    first_traded: date | None
    last_traded: date | None
    created_at: datetime


class TickerList(BaseModel):
    items: list[TickerRead]
    total: int
