from __future__ import annotations

from datetime import datetime, time, timezone, timedelta
from enum import Enum

import pytz

ET_TZ = pytz.timezone("US/Eastern")
UTC_TZ = timezone.utc

# Market session boundaries in ET
PREMARKET_START = time(4, 0)
REGULAR_START = time(9, 30)
REGULAR_END = time(16, 0)
AFTERHOURS_END = time(20, 0)


class SessionType(str, Enum):
    PREMARKET = "premarket"
    REGULAR = "regular"
    AFTERHOURS = "afterhours"
    CLOSED = "closed"


def get_et_now() -> datetime:
    return datetime.now(ET_TZ)


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = ET_TZ.localize(dt)
    return dt.astimezone(UTC_TZ)


def to_et(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(ET_TZ)


def classify_session(dt_et: datetime) -> SessionType:
    if dt_et.tzinfo is None:
        dt_et = ET_TZ.localize(dt_et)
    if dt_et.weekday() >= 5:
        return SessionType.CLOSED
    t = dt_et.time()
    if PREMARKET_START <= t < REGULAR_START:
        return SessionType.PREMARKET
    elif REGULAR_START <= t <= REGULAR_END:
        return SessionType.REGULAR
    elif REGULAR_END < t < AFTERHOURS_END:
        return SessionType.AFTERHOURS
    else:
        return SessionType.CLOSED


def is_market_open(dt_et: datetime | None = None) -> bool:
    if dt_et is None:
        dt_et = get_et_now()
    session = classify_session(dt_et)
    return session in (SessionType.REGULAR, SessionType.PREMARKET, SessionType.AFTERHOURS)


def get_market_hours_description(dt_et: datetime | None = None) -> str:
    if dt_et is None:
        dt_et = get_et_now()
    session = classify_session(dt_et)
    weekday = dt_et.weekday()
    if weekday >= 5:
        return "Market Closed (Weekend)"
    labels = {
        SessionType.PREMARKET: "Pre-Market (4:00–9:30 ET)",
        SessionType.REGULAR: "Regular Hours (9:30–16:00 ET)",
        SessionType.AFTERHOURS: "After-Hours (16:00–20:00 ET)",
        SessionType.CLOSED: "Market Closed",
    }
    return labels.get(session, "Market Closed")


def round_to_minute(dt: datetime, interval_minutes: int = 1) -> datetime:
    epoch = int(dt.timestamp())
    rounded = epoch - (epoch % (interval_minutes * 60))
    return datetime.fromtimestamp(rounded, tz=dt.tzinfo)


def get_trading_days(start: datetime, end: datetime) -> list[datetime]:
    days = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days
