from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DataHealthRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker_id: int
    status: str
    warning_type: str | None
    message: str | None
    checked_at: datetime
    provider: str | None
