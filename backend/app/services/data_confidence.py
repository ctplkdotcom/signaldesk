from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models import PriceBar, QuoteSnapshot, Ticker


class DataConfidenceService:
    """Computes a 0-100 data confidence score per ticker."""

    START_SCORE = 100
    PENALTIES = {
        "missing_data": 30,
        "stale_data": 20,
        "low_liquidity": 15,
        "wide_spread": 15,
        "ticker_mapping_warning": 20,
        "provider_fallback": 10,
        "abnormal_price_jump": 10,
    }

    async def get_confidence(self, ticker: str) -> dict:
        async with async_session_factory() as session:
            ticker_obj = (
                await session.execute(
                    select(Ticker).where(Ticker.ticker == ticker.upper())
                )
            ).scalar_one_or_none()

            if not ticker_obj:
                return {"score": 0, "breakdown": [], "label": "No Data"}

            score = self.START_SCORE
            breakdown = []

            ticker_id = ticker_obj.id
            now = datetime.now(timezone.utc)

            # Check recency of data
            last_bar = (
                await session.execute(
                    select(PriceBar)
                    .where(
                        PriceBar.ticker_id == ticker_id,
                        PriceBar.timestamp_utc >= now - timedelta(hours=24),
                    )
                    .order_by(PriceBar.timestamp_utc.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()

            if not last_bar:
                score -= self.PENALTIES["missing_data"]
                breakdown.append({"reason": "missing_data", "penalty": self.PENALTIES["missing_data"]})
            elif (now - last_bar.timestamp_utc) > timedelta(hours=1):
                score -= self.PENALTIES["stale_data"]
                breakdown.append({"reason": "stale_data", "penalty": self.PENALTIES["stale_data"]})

            # Check bar count in recent 60 minutes
            bar_count = (
                await session.execute(
                    select(sa_func.count(PriceBar.id)).where(
                        PriceBar.ticker_id == ticker_id,
                        PriceBar.timestamp_utc >= now - timedelta(hours=1),
                    )
                )
            ).scalar() or 0

            if bar_count < 5:
                score -= self.PENALTIES["low_liquidity"]
                breakdown.append({"reason": "low_liquidity", "penalty": self.PENALTIES["low_liquidity"]})

            # Check spread from latest quote
            last_quote = (
                await session.execute(
                    select(QuoteSnapshot)
                    .where(QuoteSnapshot.ticker_id == ticker_id)
                    .order_by(QuoteSnapshot.timestamp_utc.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()

            if last_quote and last_quote.bid and last_quote.ask and last_quote.bid > 0:
                spread_pct = abs(last_quote.ask - last_quote.bid) / last_quote.bid
                if spread_pct > 0.05:
                    score -= self.PENALTIES["wide_spread"]
                    breakdown.append({"reason": "wide_spread", "penalty": self.PENALTIES["wide_spread"]})

            score = max(0, min(100, score))

            if score >= 80:
                label = "Healthy"
            elif score >= 50:
                label = "Fair"
            elif score >= 20:
                label = "Warning"
            else:
                label = "Unreliable"

            return {
                "score": score,
                "label": label,
                "breakdown": breakdown,
            }
