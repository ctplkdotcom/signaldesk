from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.price_bar import PriceBar
from app.models.signal import Signal
from app.services.reference_data import ReferenceDataService
from app.utils.cache import cache


class SignalEngine:
    def __init__(self):
        self._ref_data = ReferenceDataService()

    async def generate_ma_trend_signal(self, ticker: str) -> Signal | None:
        t = await self._ref_data.get_ticker(ticker)
        if not t:
            return None

        async with async_session_factory() as session:
            result = await session.execute(
                select(PriceBar)
                .where(PriceBar.ticker_id == t.id)
                .where(PriceBar.session == "regular")
                .order_by(PriceBar.timestamp_utc.desc())
                .limit(300)
            )
            bars = list(result.scalars().all())
            bars.reverse()

        if len(bars) < 200:
            return None

        closes = np.array([b.close for b in bars], dtype=float)

        def sma(data: np.ndarray, period: int) -> np.ndarray:
            if len(data) < period:
                return np.array([])
            return np.convolve(data, np.ones(period) / period, mode="valid")

        ma50 = sma(closes, 50)
        ma200 = sma(closes, 200)

        if len(ma50) < 1 or len(ma200) < 1:
            return None

        current_ma50 = ma50[-1]
        current_ma200 = ma200[-1]
        prev_ma50 = ma50[-2] if len(ma50) >= 2 else current_ma50
        prev_ma200 = ma200[-2] if len(ma200) >= 2 else current_ma200

        direction = "neutral"
        confidence = 0.0
        strength = 0.0
        explanation = ""

        if current_ma50 > current_ma200 and prev_ma50 <= prev_ma200:
            direction = "bullish"
            spread = (current_ma50 - current_ma200) / current_ma200
            confidence = min(0.9, 0.5 + spread * 10)
            strength = spread * 100
            explanation = (
                f"50-day MA ({current_ma50:.2f}) crossed above 200-day MA ({current_ma200:.2f}). "
                f"Golden cross. Spread: {spread*100:.2f}%"
            )
        elif current_ma50 < current_ma200 and prev_ma50 >= prev_ma200:
            direction = "bearish"
            spread = (current_ma200 - current_ma50) / current_ma200
            confidence = min(0.9, 0.5 + spread * 10)
            strength = -spread * 100
            explanation = (
                f"50-day MA ({current_ma50:.2f}) crossed below 200-day MA ({current_ma200:.2f}). "
                f"Death cross. Spread: {spread*100:.2f}%"
            )
        elif current_ma50 > current_ma200:
            direction = "bullish"
            spread = (current_ma50 - current_ma200) / current_ma200
            confidence = min(0.6, 0.3 + spread * 5)
            strength = spread * 50
            explanation = (
                f"50-day MA ({current_ma50:.2f}) above 200-day MA ({current_ma200:.2f}). "
                f"Uptrend maintained. Spread: {spread*100:.2f}%"
            )
        elif current_ma50 < current_ma200:
            direction = "bearish"
            spread = (current_ma200 - current_ma50) / current_ma200
            confidence = min(0.6, 0.3 + spread * 5)
            strength = -spread * 50
            explanation = (
                f"50-day MA ({current_ma50:.2f}) below 200-day MA ({current_ma200:.2f}). "
                f"Downtrend maintained. Spread: {spread*100:.2f}%"
            )

        if direction == "neutral":
            return None

        async with async_session_factory() as session:
            signal = Signal(
                ticker_id=t.id,
                strategy_type="ma_trend_following",
                direction=direction,
                confidence=round(confidence, 4),
                strength=round(strength, 4),
                explanation=explanation,
                data_sources={"last_bar_utc": str(bars[-1].timestamp_utc) if bars else None},
            )
            session.add(signal)
            await session.commit()
            await session.refresh(signal)
            return signal

    async def get_latest_signal(self, ticker: str) -> Signal | None:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Signal)
                .where(Signal.ticker.has(ticker=ticker.upper()))
                .order_by(desc(Signal.generated_at))
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def get_signals(self, ticker: str | None = None, limit: int = 50) -> list[Signal]:
        async with async_session_factory() as session:
            query = select(Signal)
            if ticker:
                query = query.where(Signal.ticker.has(ticker=ticker.upper()))
            query = query.order_by(desc(Signal.generated_at)).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())
