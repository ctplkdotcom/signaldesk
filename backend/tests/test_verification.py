import pytest

from app.services.verification import (
    get_verification_links,
    get_verification_config,
    _is_safe_url,
)


class TestVerificationURLSafety:
    def test_accepts_https_yahoo(self):
        assert _is_safe_url("https://finance.yahoo.com/quote/MU")

    def test_accepts_https_marketwatch(self):
        assert _is_safe_url("https://www.marketwatch.com/investing/stock/MU")

    def test_accepts_https_google_finance(self):
        assert _is_safe_url("https://www.google.com/finance/quote/MU")

    def test_accepts_https_vanguard(self):
        assert _is_safe_url("https://investor.vanguard.com/investment-products/etfs/profile/voo")

    def test_rejects_http(self):
        assert not _is_safe_url("http://finance.yahoo.com/quote/MU")

    def test_rejects_unknown_domain(self):
        assert not _is_safe_url("https://evil.example.com/quote/MU")

    def test_rejects_empty_url(self):
        assert not _is_safe_url("")

    def test_rejects_malformed_url(self):
        assert not _is_safe_url("not-a-url")

    def test_accepts_uppercase_domain(self):
        assert _is_safe_url("https://FINANCE.YAHOO.COM/quote/MU")

    def test_accepts_uppercase_url(self):
        assert _is_safe_url("HTTPS://FINANCE.YAHOO.COM/QUOTE/AAPL")


class TestVerificationLinks:
    def test_returns_links_for_common_ticker(self):
        links = get_verification_links("MU")
        sources = {l["source"] for l in links}
        assert "Yahoo Finance" in sources
        assert "MarketWatch" in sources
        assert "Google Finance" in sources
        assert len(links) == 3

    def test_returns_links_case_insensitive(self):
        links = get_verification_links("mu")
        assert len(links) == 3

    def test_strips_whitespace(self):
        links = get_verification_links("  AAPL  ")
        assert len(links) == 3

    def test_includes_vanguard_override_for_voo(self):
        links = get_verification_links("VOO")
        sources = {l["source"] for l in links}
        assert "Vanguard" in sources
        assert "Yahoo Finance" in sources

    def test_vanguard_url_is_correct_for_voo(self):
        links = get_verification_links("VOO")
        vanguard = [l for l in links if l["source"] == "Vanguard"][0]
        assert vanguard["url"] == "https://investor.vanguard.com/investment-products/etfs/profile/voo"

    def test_no_duplicate_urls(self):
        links = get_verification_links("VOO")
        urls = [l["url"] for l in links]
        assert len(urls) == len(set(urls))

    def test_all_urls_are_safe(self):
        links = get_verification_links("AAPL")
        for link in links:
            assert _is_safe_url(link["url"])


class TestVerificationConfig:
    def test_returns_full_config(self):
        cfg = get_verification_config("MU")
        assert cfg["ticker"] == "MU"
        assert len(cfg["verification_links"]) > 0
        assert cfg["preferred_verification_source"] == "Yahoo Finance"
        assert cfg["verification_supported"] is True

    def test_preferred_source_is_first(self):
        cfg = get_verification_config("VOO")
        assert cfg["preferred_verification_source"] == "Vanguard"

    def test_config_for_unknown_ticker(self):
        cfg = get_verification_config("ZZZZZ")
        assert cfg["ticker"] == "ZZZZZ"
        assert len(cfg["verification_links"]) > 0
        assert cfg["verification_supported"] is True

    def test_ticker_uppercased(self):
        cfg = get_verification_config("mu")
        assert cfg["ticker"] == "MU"


class TestVerificationAPI:
    @pytest.mark.asyncio
    async def test_verification_endpoint_returns_links(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/tickers/MU/verification")
            assert resp.status_code == 200
            data = resp.json()
            assert data["ticker"] == "MU"
            assert len(data["verification_links"]) >= 3
            assert data["verification_supported"] is True

    @pytest.mark.asyncio
    async def test_verification_endpoint_case_insensitive(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/tickers/voo/verification")
            assert resp.status_code == 200
            data = resp.json()
            assert data["ticker"] == "VOO"
            sources = [l["source"] for l in data["verification_links"]]
            assert "Vanguard" in sources

    @pytest.mark.asyncio
    async def test_verification_urls_are_safe(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/tickers/AAPL/verification")
            data = resp.json()
            for link in data["verification_links"]:
                assert link["url"].startswith("https://")
                assert _is_safe_url(link["url"])
