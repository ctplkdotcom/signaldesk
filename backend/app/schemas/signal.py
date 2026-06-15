from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker_id: int
    generated_at: datetime
    valid_until: datetime | None
    strategy_type: str
    direction: str
    confidence: float
    strength: float
    explanation: str | None


class SignalList(BaseModel):
    items: list[SignalRead]
    total: int
