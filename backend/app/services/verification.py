from __future__ import annotations

from urllib.parse import urlparse

VERIFICATION_PROVIDERS: list[dict[str, str]] = [
    {"source": "Yahoo Finance", "url_template": "https://finance.yahoo.com/quote/{ticker}"},
    {"source": "MarketWatch", "url_template": "https://www.marketwatch.com/investing/stock/{ticker}"},
    {"source": "Google Finance", "url_template": "https://www.google.com/finance/quote/{ticker}"},
]

ALLOWED_DOMAINS: set[str] = {
    "finance.yahoo.com",
    "www.marketwatch.com",
    "www.google.com",
    "investor.vanguard.com",
}

TICKER_OVERRIDES: dict[str, list[dict[str, str]]] = {
    "VOO": [
        {"source": "Vanguard", "url": "https://investor.vanguard.com/investment-products/etfs/profile/voo"},
    ],
}


def _is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("https",):
            return False
        if parsed.netloc.lower() not in ALLOWED_DOMAINS:
            return False
        return True
    except Exception:
        return False


def get_verification_links(ticker: str) -> list[dict[str, str]]:
    ticker = ticker.upper().strip()
    links: list[dict[str, str]] = []

    overrides = TICKER_OVERRIDES.get(ticker)
    if overrides:
        for link in overrides:
            if _is_safe_url(link["url"]):
                links.append({"source": link["source"], "url": link["url"]})

    for provider in VERIFICATION_PROVIDERS:
        url = provider["url_template"].replace("{ticker}", ticker)
        if _is_safe_url(url):
            if not any(l["url"] == url for l in links):
                links.append({"source": provider["source"], "url": url})

    return links


def get_verification_config(ticker: str) -> dict:
    links = get_verification_links(ticker)
    preferred = links[0]["source"] if links else None
    return {
        "ticker": ticker.upper(),
        "verification_links": links,
        "preferred_verification_source": preferred,
        "verification_supported": len(links) > 0,
    }
