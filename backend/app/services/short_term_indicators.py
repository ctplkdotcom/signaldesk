from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models import CleanPriceBar, Ticker


class ShortTermIndicatorService:
    """Computes 1-min, 5-min, 10-min price/volume indicators."""

    async def get_indicators(self, ticker: str) -> dict:
        async with async_session_factory() as session:
            ticker_obj = (
                await session.execute(
                    select(Ticker).where(Ticker.ticker == ticker.upper())
                )
            ).scalar_one_or_none()

            if not ticker_obj:
                return {"error": "Ticker not found"}

            now = datetime.now(timezone.utc)
            bars = await self._get_recent_bars(session, ticker_obj.id, now, minutes=10)

            if len(bars) < 2:
                return {
                    "ticker": ticker.upper(),
                    "bars_available": len(bars),
                    "status": "insufficient_data",
                }

            current = bars[-1]
            bar_1min_ago = bars[-2] if len(bars) >= 2 else None
            bar_5min_ago = bars[-5] if len(bars) >= 5 else bars[0]
            bar_10min_ago = bars[-10] if len(bars) >= 10 else bars[0]

            price_change_1m = self._calc_change(bar_1min_ago, current) if bar_1min_ago else None
            price_change_5m = self._calc_change(bar_5min_ago, current)
            price_change_10m = self._calc_change(bar_10min_ago, current)

            vwap = self._calc_vwap(bars)
            vwap_distance = ((current.close - vwap) / vwap * 100) if vwap else None

            avg_volume_5m = self._avg_volume(bars[-5:]) if len(bars) >= 5 else None
            avg_volume_10m = self._avg_volume(bars)
            volume_spike_5m = None
            if avg_volume_5m and len(bars) >= 2:
                vol_5m_ago = self._avg_volume(bars[-6:-1]) if len(bars) >= 6 else avg_volume_5m
                volume_spike_5m = ((avg_volume_5m - vol_5m_ago) / vol_5m_ago * 100) if vol_5m_ago else None

            direction = self._classify_direction(
                price_change_5m, price_change_1m, vwap_distance, volume_spike_5m
            )

            return {
                "ticker": ticker.upper(),
                "bars_available": len(bars),
                "current_price": current.close,
                "current_volume": current.volume,
                "change_1m_pct": price_change_1m,
                "change_5m_pct": price_change_5m,
                "change_10m_pct": price_change_10m,
                "vwap": round(vwap, 2),
                "vwap_distance_pct": round(vwap_distance, 2) if vwap_distance is not None else None,
                "volume_spike_5m_pct": round(volume_spike_5m, 2) if volume_spike_5m is not None else None,
                "short_term_direction": direction,
                "timestamp": now.isoformat(),
            }

    async def _get_recent_bars(
        self, session: AsyncSession, ticker_id: int, now: datetime, minutes: int
    ) -> list:
        stmt = (
            select(CleanPriceBar)
            .where(
                CleanPriceBar.ticker_id == ticker_id,
                CleanPriceBar.timestamp_utc >= now - timedelta(minutes=minutes + 1),
            )
            .order_by(CleanPriceBar.timestamp_utc.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    def _calc_change(self, bar_old, bar_new) -> float:
        if bar_old.close == 0:
            return 0.0
        return round((bar_new.close - bar_old.close) / bar_old.close * 100, 2)

    def _calc_vwap(self, bars: list) -> float:
        total_pv = sum(b.close * b.volume for b in bars if b.volume > 0)
        total_v = sum(b.volume for b in bars if b.volume > 0)
        return total_pv / total_v if total_v > 0 else bars[-1].close

    def _avg_volume(self, bars: list) -> float:
        return sum(b.volume for b in bars) / len(bars) if bars else 0

    def _classify_direction(
        self,
        change_5m: float | None,
        change_1m: float | None,
        vwap_dist: float | None,
        vol_spike: float | None,
    ) -> str:
        bullish = 0
        bearish = 0

        if change_5m is not None:
            if change_5m > 0.3:
                bullish += 1
            elif change_5m < -0.3:
                bearish += 1

        if change_1m is not None:
            if change_1m > 0.1:
                bullish += 1
            elif change_1m < -0.1:
                bearish += 1

        if vwap_dist is not None:
            if vwap_dist > 0.2:
                bullish += 1
            elif vwap_dist < -0.2:
                bearish += 1

        if vol_spike is not None:
            if vol_spike > 30:
                bullish += 1
            elif vol_spike < -30:
                bearish += 1

        if bullish > bearish:
            return "Short-Term Bullish"
        elif bearish > bullish:
            return "Short-Term Bearish"
        return "Neutral"
