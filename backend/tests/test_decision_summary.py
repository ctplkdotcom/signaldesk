from types import SimpleNamespace

import pytest

from app.api.tickers import _build_decision_summary


def _signal(direction="bullish", confidence=0.75, explanation="MA trend up"):
    return SimpleNamespace(
        direction=direction,
        confidence=confidence,
        explanation=explanation,
    )


def _health(status="healthy", warning_type=None, message="All good"):
    return SimpleNamespace(
        status=status,
        warning_type=warning_type,
        message=message,
    )


def _news_article(score: float):
    return SimpleNamespace(
        scored_news=SimpleNamespace(final_score=score),
    )


class TestBuildDecisionSummarySignal:
    def test_bullish_signal_healthy_data(self):
        result = _build_decision_summary(
            ticker="MU",
            signal_obj=_signal("bullish", 0.8),
            health=_health("healthy"),
        )
        assert result["overall_direction"] == "bullish"
        assert result["composite_confidence"] == 0.8
        assert "BULLISH" in result["explanation"]

    def test_bearish_signal_healthy_data(self):
        result = _build_decision_summary(
            ticker="AAPL",
            signal_obj=_signal("bearish", 0.65),
            health=_health("healthy"),
        )
        assert result["overall_direction"] == "bearish"
        assert result["composite_confidence"] == 0.65
        assert "BEARISH" in result["explanation"]

    def test_no_signal_neutral_direction(self):
        result = _build_decision_summary(ticker="VOO")
        assert result["overall_direction"] == "neutral"
        assert result["composite_confidence"] == 0.0
        assert "No active signal" in result["explanation"]

    def test_low_confidence_downgrades_overall(self):
        result = _build_decision_summary(
            ticker="SNDK",
            signal_obj=_signal("bullish", 0.3),
            health=_health("healthy"),
        )
        assert result["overall_direction"] == "neutral"
        assert result["signal"]["direction"] == "bullish"
        assert result["composite_confidence"] == 0.3


class TestBuildDecisionSummaryHealth:
    def test_unhealthy_data_warning_in_explanation(self):
        result = _build_decision_summary(
            ticker="MU",
            signal_obj=_signal("bullish", 0.8),
            health=_health("warning", "stale_data", "Data is 2 hours old"),
        )
        assert result["overall_direction"] == "neutral"
        assert "Data warning: stale_data" in result["explanation"]
        assert result["data_health"]["warning_type"] == "stale_data"

    def test_unknown_health_downgrades_to_neutral(self):
        result = _build_decision_summary(
            ticker="MU",
            signal_obj=_signal("bullish", 0.8),
        )
        assert result["overall_direction"] == "neutral"
        assert result["data_health"]["status"] == "unknown"
        assert "Data health unknown" in result["explanation"]


class TestBuildDecisionSummaryNews:
    def test_positive_news_sentiment(self):
        result = _build_decision_summary(
            ticker="MU",
            signal_obj=_signal("bullish", 0.8),
            health=_health("healthy"),
            news_articles=[_news_article(0.5), _news_article(0.7)],
        )
        assert result["news_sentiment_avg"] == 0.6
        assert result["news_article_count"] == 2
        assert "positive" in result["explanation"]

    def test_negative_news_sentiment(self):
        result = _build_decision_summary(
            ticker="AAPL",
            signal_obj=_signal("bearish", 0.6),
            health=_health("healthy"),
            news_articles=[_news_article(-0.8), _news_article(-0.4)],
        )
        assert result["news_sentiment_avg"] == -0.6
        assert "negative" in result["explanation"]

    def test_mixed_news_sentiment_neutral(self):
        result = _build_decision_summary(
            ticker="VOO",
            news_articles=[_news_article(0.3), _news_article(-0.3)],
        )
        assert result["news_sentiment_avg"] == 0.0
        assert "neutral" in result["explanation"]

    def test_no_news_empty_explanation(self):
        result = _build_decision_summary(
            ticker="MU",
            signal_obj=_signal("bullish", 0.8),
            health=_health("healthy"),
        )
        assert result["news_article_count"] == 0
        assert "No recent news" in result["explanation"]

    def test_news_articles_without_scored_news(self):
        article = SimpleNamespace(scored_news=None)
        result = _build_decision_summary(
            ticker="MU",
            signal_obj=_signal("bullish", 0.8),
            health=_health("healthy"),
            news_articles=[article],
        )
        assert result["news_article_count"] == 1
        assert result["news_sentiment_avg"] == 0.0


class TestBuildDecisionSummaryQuote:
    def test_quote_included_in_result(self):
        quote = {"price": 95.5, "timestamp_utc": "2026-06-12T15:30:00Z"}
        result = _build_decision_summary(
            ticker="MU",
            quote=quote,
            signal_obj=_signal("bullish", 0.8),
            health=_health("healthy"),
        )
        assert result["current_price"] == 95.5
        assert result["price_updated_utc"] == "2026-06-12T15:30:00Z"

    def test_no_quote_returns_none(self):
        result = _build_decision_summary(ticker="MU")
        assert result["current_price"] is None
        assert result["price_updated_utc"] is None


class TestDecisionSummaryAPI:
    @pytest.mark.asyncio
    async def test_endpoint_returns_valid_structure(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/tickers/MU/decision-summary")
            assert resp.status_code == 200
            data = resp.json()
            assert data["ticker"] == "MU"
            assert data["overall_direction"] in ("bullish", "bearish", "neutral")
            assert isinstance(data["composite_confidence"], float)
            assert isinstance(data["explanation"], str)

    @pytest.mark.asyncio
    async def test_endpoint_downcases_ticker(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/tickers/aapl/decision-summary")
            assert resp.status_code == 200
            data = resp.json()
            assert data["ticker"] == "AAPL"

    @pytest.mark.asyncio
    async def test_endpoint_returns_quote_field(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/tickers/MU/decision-summary")
            data = resp.json()
            assert "current_price" in data
            assert "price_updated_utc" in data

    @pytest.mark.asyncio
    async def test_endpoint_is_deterministic(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r1 = await ac.get("/api/v1/tickers/MU/decision-summary")
            r2 = await ac.get("/api/v1/tickers/MU/decision-summary")
            assert r1.json() == r2.json()
