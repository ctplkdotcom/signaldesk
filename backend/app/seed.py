"""Seed initial reference data.

Run: python -m app.seed
"""

import asyncio
from datetime import date

INITIAL_TICKERS = [
    {
        "ticker": "MU",
        "name": "Micron Technology, Inc.",
        "asset_type": "stock",
        "exchange": "NASDAQ",
        "is_active": True,
        "first_traded": "1994-01-03",
    },
    {
        "ticker": "VOO",
        "name": "Vanguard S&P 500 ETF",
        "asset_type": "etf",
        "exchange": "NYSE Arca",
        "is_active": True,
        "first_traded": "2010-09-09",
    },
    {
        "ticker": "SNDK",
        "name": "SanDisk Corporation",
        "asset_type": "stock",
        "exchange": "NASDAQ",
        "is_active": False,
        "first_traded": "1995-11-01",
        "last_traded": "2016-05-12",
        "provider_mappings": {
            "polygon": "SNDK",
            "note": "Acquired by Western Digital in 2016. Historical data only.",
        },
    },
    {
        "ticker": "AMD",
        "name": "Advanced Micro Devices Inc.",
        "asset_type": "stock",
        "exchange": "NASDAQ",
        "is_active": True,
        "first_traded": "1980-03-17",
        "provider_mappings": {
            "polygon": "AMD",
        },
    },
]

METHODOLOGIES = [
    {
        "name": "Short-Term Momentum v1",
        "version": "1.0",
        "description": "5-minute momentum strategy using 1-min bar close prices. Enters long when 5-min momentum exceeds 0.5%, exits when momentum reverses below -0.3%.",
        "input_data": {"bars": "1-minute OHLCV", "lookback": "5 periods"},
        "formula": "momentum = (close[t] - close[t-5]) / close[t-5]",
        "assumptions": {"slippage": "0.1%", "fee": "0.1%", "liquidity": "sufficient for retail"},
        "limitations": {"does_not_account_for": "gap risk, news events, extended hours"},
    },
    {
        "name": "VWAP Confirmation v1",
        "version": "1.0",
        "description": "VWAP reversion strategy. Buys when price deviates more than 0.3% below VWAP, sells when deviation narrows.",
        "input_data": {"bars": "1-minute OHLCV", "vwap_window": "10 periods"},
        "formula": "deviation = (close - vwap) / vwap",
        "assumptions": {"mean_reversion": "prices tend to revert to VWAP intraday"},
        "limitations": {"fails_during": "strong trend days, news-driven breakouts"},
    },
    {
        "name": "Data Confidence Score v1",
        "version": "1.0",
        "description": "Scoring system for data quality. Starts at 100, deducts for missing data, staleness, low liquidity, wide spreads.",
        "input_data": {"bars": "1-minute bars", "quotes": "latest snapshot", "age": "last 24 hours"},
        "formula": "score = 100 - penalties(age, count, spread)",
        "assumptions": {"fresh_data": "bars within 1 hour = healthy"},
        "limitations": {"does_not_detect": "incorrect data, split/adjustment errors"},
    },
    {
        "name": "News Score v1",
        "version": "1.0",
        "description": "Multi-factor news scoring using sentiment, event type, source reliability, and recency decay.",
        "input_data": {"article": "title, source, event_type, published_at"},
        "formula": "final = 0.4*sentiment + 0.3*event + 0.2*source + 0.1*recency",
        "assumptions": {"sentiment_lexicon": "financial domain specific"},
        "limitations": {"may_miss": "nuanced context, sarcasm, regulatory filings"},
    },
    {
        "name": "MA Trend v1",
        "version": "1.0",
        "description": "50/200 day SMA crossover strategy. Golden cross = bullish, death cross = bearish.",
        "input_data": {"bars": "daily close prices", "periods": "50 and 200 days"},
        "formula": "signal = bullish if SMA(50) > SMA(200), bearish otherwise",
        "assumptions": {"trend_following": "trends persist once established"},
        "limitations": {"lagging_indicator": "late entries/exits in fast markets"},
    },
]


async def seed():
    from app.database import init_db, async_session_factory
    from app.models.ticker import Ticker
    from app.models.watchlist import WatchlistItem
    from app.models.methodology import Methodology
    from sqlalchemy import select

    await init_db()
    print("Database initialized")

    async with async_session_factory() as session:
        for t_data in INITIAL_TICKERS:
            result = await session.execute(select(Ticker).where(Ticker.ticker == t_data["ticker"]))
            if result.scalar_one_or_none():
                print(f"  Skipped existing ticker: {t_data['ticker']}")
                continue

            t = Ticker(
                ticker=t_data["ticker"],
                name=t_data.get("name"),
                asset_type=t_data.get("asset_type"),
                exchange=t_data.get("exchange"),
                currency=t_data.get("currency", "USD"),
                is_active=t_data.get("is_active", True),
                first_traded=date.fromisoformat(t_data["first_traded"]) if isinstance(t_data.get("first_traded"), str) else t_data.get("first_traded"),
                last_traded=date.fromisoformat(t_data["last_traded"]) if isinstance(t_data.get("last_traded"), str) else t_data.get("last_traded"),
                provider_mappings=t_data.get("provider_mappings"),
            )
            session.add(t)
            await session.flush()

            wl = WatchlistItem(ticker_id=t.id)
            session.add(wl)
            print(f"  Created ticker: {t_data['ticker']}")

        for m_data in METHODOLOGIES:
            result = await session.execute(
                select(Methodology).where(Methodology.name == m_data["name"])
            )
            if result.scalar_one_or_none():
                print(f"  Skipped existing methodology: {m_data['name']}")
                continue

            m = Methodology(**m_data)
            session.add(m)
            print(f"  Created methodology: {m_data['name']}")

        await session.commit()

    print("Seed complete")


if __name__ == "__main__":
    asyncio.run(seed())
