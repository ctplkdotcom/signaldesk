from __future__ import annotations

from app.utils.time import SessionType

SESSION_SLIPPAGE_MAP = {
    SessionType.REGULAR: 0.001,
    SessionType.PREMARKET: 0.003,
    SessionType.AFTERHOURS: 0.003,
    SessionType.CLOSED: 0.005,
}

SESSION_LABELS = {
    SessionType.REGULAR: "Regular Hours",
    SessionType.PREMARKET: "Pre-Market",
    SessionType.AFTERHOURS: "After-Hours",
    SessionType.CLOSED: "Closed",
}

SESSION_ORDER = [
    SessionType.PREMARKET,
    SessionType.REGULAR,
    SessionType.AFTERHOURS,
    SessionType.CLOSED,
]
