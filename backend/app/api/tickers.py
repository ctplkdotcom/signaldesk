from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.services.reference_data import ReferenceDataService
from app.services.market_data import MarketDataService
from app.services.signal_engine import SignalEngine
from app.services.data_health import DataHealthService
from app.services.verification import get_verification_config

router = APIRouter()
ref_data = ReferenceDataService()
market_data = MarketDataService()
signal_engine = SignalEngine()
data_health = DataHealthService()


@router.get("")
async def list_tickers(active_only: bool = True):
    tickers = await ref_data.list_tickers(active_only=active_only)
    return {
        "items": [
            {
                "id": t.id,
                "ticker": t.ticker,
                "name": t.name,
                "asset_type": t.asset_type,
                "exchange": t.exchange,
                "is_active": t.is_active,
            }
            for t in tickers
        ],
        "total": len(tickers),
    }


@router.get("/{ticker}")
async def get_ticker(ticker: str):
    t = await ref_data.get_ticker(ticker.upper())
    if not t:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
    return {
        "id": t.id,
        "ticker": t.ticker,
        "name": t.name,
        "asset_type": t.asset_type,
        "exchange": t.exchange,
        "currency": t.currency,
        "is_active": t.is_active,
    }


@router.get("/{ticker}/price")
async def get_price(ticker: str):
    quote = await market_data.get_latest_quote(ticker.upper())
    health = await data_health.get_ticker_health(ticker.upper())
    signal = await signal_engine.get_latest_signal(ticker.upper())

    if not quote:
        raise HTTPException(status_code=404, detail=f"No price data for {ticker}")

    return {
        "ticker": ticker.upper(),
        "price": quote.get("price"),
        "open": quote.get("open"),
        "high": quote.get("high"),
        "low": quote.get("low"),
        "volume": quote.get("volume"),
        "bid": quote.get("bid"),
        "ask": quote.get("ask"),
        "session": quote.get("session"),
        "updated_utc": quote.get("timestamp_utc"),
        "updated_et": quote.get("timestamp_et"),
        "provider": quote.get("provider"),
        "signal": {
            "direction": signal.direction if signal else "neutral",
            "confidence": signal.confidence if signal else 0,
            "strategy": signal.strategy_type if signal else None,
        } if signal else None,
        "health": {
            "status": health.status if health else "unknown",
            "warning": health.warning_type if health else None,
            "message": health.message if health else None,
        } if health else None,
    }


@router.get("/{ticker}/bars")
async def get_bars(
    ticker: str,
    start: str | None = None,
    end: str | None = None,
    timespan: str = "minute",
    limit: int = 1000,
):
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt = datetime.fromisoformat(end) if end else None

    bars = await market_data.get_bars(
        ticker.upper(),
        start=start_dt,
        end=end_dt,
        timespan=timespan,
        limit=limit,
    )

    return {
        "ticker": ticker.upper(),
        "count": len(bars),
        "items": [
            {
                "timestamp_utc": str(b.timestamp_utc),
                "timestamp_et": str(b.timestamp_et),
                "session": b.session,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
            }
            for b in bars
        ],
    }


@router.get("/{ticker}/signals")
async def get_ticker_signals(ticker: str, limit: int = 20):
    signals = await signal_engine.get_signals(ticker=ticker.upper(), limit=limit)
    return {
        "ticker": ticker.upper(),
        "count": len(signals),
        "items": [
            {
                "id": s.id,
                "strategy_type": s.strategy_type,
                "direction": s.direction,
                "confidence": s.confidence,
                "strength": s.strength,
                "explanation": s.explanation,
                "generated_at": str(s.generated_at),
            }
            for s in signals
        ],
    }


@router.get("/{ticker}/health")
async def get_ticker_health(ticker: str):
    health = await data_health.get_ticker_health(ticker.upper())
    if not health:
        health = await data_health.check_ticker_health(ticker.upper())
    return {
        "ticker": ticker.upper(),
        "status": health.status,
        "warning_type": health.warning_type,
        "message": health.message,
        "checked_at": str(health.checked_at),
        "provider": health.provider,
    }


@router.post("/{ticker}/refresh")
async def refresh_ticker(ticker: str):
    await data_health.check_ticker_health(ticker.upper())
    signal = await signal_engine.generate_ma_trend_signal(ticker.upper())
    return {
        "ticker": ticker.upper(),
        "signal_generated": signal is not None,
        "signal_direction": signal.direction if signal else None,
        "message": f"Refreshed data and MA trend signal for {ticker.upper()}",
    }


@router.get("/{ticker}/decision-summary")
async def get_ticker_decision_summary(ticker: str):
    ticker = ticker.upper()

    quote = None
    signal = None
    health = None
    news_articles = []

    try:
        quote = await market_data.get_latest_quote(ticker)
    except Exception:
        pass

    try:
        signal = await signal_engine.get_latest_signal(ticker)
    except Exception:
        pass

    try:
        health = await data_health.get_ticker_health(ticker)
        if not health:
            health = await data_health.check_ticker_health(ticker)
    except Exception:
        pass

    try:
        from app.services.news_service import NewsService
        news_svc = NewsService()
        news_result = await news_svc.get_news(ticker=ticker, limit=10)
        news_articles = list(news_result) if news_result else []
    except Exception:
        pass

    return _build_decision_summary(
        ticker=ticker,
        quote=quote,
        signal_obj=signal,
        health=health,
        news_articles=news_articles,
    )


def _build_decision_summary(
    ticker: str,
    quote: dict | None = None,
    signal_obj=None,
    health=None,
    news_articles: list | None = None,
) -> dict:
    news_articles = news_articles or []

    signal_confidence = signal_obj.confidence if signal_obj else 0.0
    signal_direction = signal_obj.direction if signal_obj else "neutral"

    health_status = health.status if health else "unknown"
    data_healthy = 1.0 if health_status == "healthy" else 0.5

    composite_confidence = round(signal_confidence * data_healthy, 4)

    news_sentiment_avg = 0.0
    news_article_count = len(news_articles)
    if news_articles:
        scores = []
        for article in news_articles:
            if hasattr(article, "scored_news") and article.scored_news:
                scores.append(article.scored_news.final_score)
        if scores:
            news_sentiment_avg = round(sum(scores) / len(scores), 2)

    parts = []
    if signal_obj and signal_direction != "neutral":
        parts.append(
            f"{signal_direction.upper()} signal active ({int(signal_confidence * 100)}% confidence)"
        )
    else:
        parts.append("No active signal")

    if health:
        if health_status == "healthy":
            parts.append("Data is current")
        else:
            parts.append(f"Data warning: {health.warning_type or health_status}")
    else:
        parts.append("Data health unknown")

    if news_articles:
        if news_sentiment_avg > 0:
            sentiment_label = "positive"
        elif news_sentiment_avg < 0:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        parts.append(f"News sentiment is {sentiment_label} ({news_sentiment_avg:+.2f})")
    else:
        parts.append("No recent news")

    explanation = " · ".join(parts)

    if signal_obj and signal_direction != "neutral" and composite_confidence >= 0.5 and health_status == "healthy":
        overall_direction = signal_direction
    else:
        overall_direction = "neutral"

    return {
        "ticker": ticker,
        "overall_direction": overall_direction,
        "composite_confidence": composite_confidence,
        "explanation": explanation,
        "signal": {
            "direction": signal_direction,
            "confidence": signal_confidence,
            "explanation": signal_obj.explanation if signal_obj else None,
        } if signal_obj else None,
        "data_health": {
            "status": health_status,
            "warning_type": health.warning_type if health else None,
            "message": health.message if health else None,
        },
        "news_sentiment_avg": news_sentiment_avg,
        "news_article_count": news_article_count,
        "current_price": quote.get("price") if quote else None,
        "price_updated_utc": quote.get("timestamp_utc") if quote else None,
    }


@router.get("/{ticker}/verification")
async def get_ticker_verification(ticker: str):
    return get_verification_config(ticker.upper())
