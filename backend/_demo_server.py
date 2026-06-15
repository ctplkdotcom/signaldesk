"""Standalone demo server — all API endpoints mocked, no DB needed."""
import logging
import os
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.tickers import _build_decision_summary
from app.services.verification import get_verification_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("signal-desk-demo")

app = FastAPI(title="Signal Desk — Demo Server")

_cors_origins = os.getenv("CORS_ORIGINS", "")
_ALLOWED_ORIGINS = (
    [o.strip() for o in _cors_origins.split(",") if o.strip()]
    if _cors_origins
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Mock Data ──────────────────────────────────────────────────────────────

TICKERS = {
    "MU": {
        "id": 1, "ticker": "MU", "name": "Micron Technology Inc.",
        "asset_type": "stock", "exchange": "NASDAQ", "currency": "USD",
        "is_active": True,
    },
    "VOO": {
        "id": 2, "ticker": "VOO", "name": "Vanguard S&P 500 ETF",
        "asset_type": "etf", "exchange": "NYSEARCA", "currency": "USD",
        "is_active": True,
    },
    "SNDK": {
        "id": 3, "ticker": "SNDK", "name": "SanDisk Corporation",
        "asset_type": "stock", "exchange": "NASDAQ", "currency": "USD",
        "is_active": True,
    },
    "NOK": {
        "id": 4, "ticker": "NOK", "name": "Nokia Oyj",
        "asset_type": "stock", "exchange": "NYSE", "currency": "USD",
        "is_active": True,
    },
    "SQQQ": {
        "id": 5, "ticker": "SQQQ", "name": "ProShares UltraPro Short QQQ",
        "asset_type": "etf", "exchange": "NASDAQ", "currency": "USD",
        "is_active": True,
    },
}

PRICES = {
    "MU": {
        "price": 981.01, "open": 904.37, "high": 996.77, "low": 895.50,
        "volume": 56337333, "bid": 975.03, "ask": 986.55, "session": "PREMARKET",
        "provider": "Polygon.io",
        "previous_close": 891.88, "change_percent": -1.49,
    },
    "VOO": {
        "price": 680.38, "open": 670.10, "high": 680.36, "low": 666.08,
        "volume": 7071988, "bid": 677.90, "ask": 678.80, "session": "PREMARKET",
        "provider": "Polygon.io",
        "previous_close": 667.05, "change_percent": 0.32,
    },
    "SNDK": {
        "price": 1879.09, "open": 1672.26, "high": 1895.00, "low": 1665.00,
        "volume": 13440811, "bid": 1860.00, "ask": 1830.00, "session": "PREMARKET",
        "provider": "Polygon.io",
        "previous_close": 1643.23, "change_percent": -0.13,
    },
    "NOK": {
        "price": 14.40, "open": 13.57, "high": 14.17, "low": 13.40,
        "volume": 92824172, "bid": 14.38, "ask": 14.42, "session": "PREMARKET",
        "provider": "Polygon.io",
        "previous_close": 13.40, "change_percent": 2.13,
    },
    "SQQQ": {
        "price": 40.60, "open": 44.19, "high": 45.01, "low": 40.44,
        "volume": 119057206, "bid": 40.73, "ask": 40.77, "session": "PREMARKET",
        "provider": "Polygon.io",
        "previous_close": 45.25, "change_percent": -0.56,
    },
}

BARS = {
    "MU": [
        {"o": 964.50, "h": 966.80, "l": 962.30, "c": 965.65, "v": 5200000},
        {"o": 965.65, "h": 968.95, "l": 964.50, "c": 967.80, "v": 4800000},
        {"o": 967.80, "h": 970.10, "l": 966.70, "c": 969.00, "v": 5100000},
        {"o": 969.00, "h": 972.30, "l": 968.85, "c": 971.15, "v": 4900000},
        {"o": 971.15, "h": 974.45, "l": 970.00, "c": 973.30, "v": 5300000},
        {"o": 973.30, "h": 976.60, "l": 972.10, "c": 975.40, "v": 4700000},
        {"o": 975.40, "h": 978.70, "l": 974.20, "c": 977.55, "v": 5000000},
        {"o": 977.55, "h": 980.85, "l": 976.35, "c": 979.70, "v": 4850000},
        {"o": 979.70, "h": 982.95, "l": 978.50, "c": 981.80, "v": 5100000},
        {"o": 981.80, "h": 984.00, "l": 980.60, "c": 983.85, "v": 4950000},
    ],
    "VOO": [
        {"o": 670.50, "h": 671.90, "l": 669.20, "c": 670.70, "v": 2100000},
        {"o": 670.70, "h": 672.10, "l": 669.50, "c": 671.95, "v": 1950000},
        {"o": 671.95, "h": 673.40, "l": 670.80, "c": 673.20, "v": 2200000},
        {"o": 673.20, "h": 674.60, "l": 672.00, "c": 674.40, "v": 2050000},
        {"o": 674.40, "h": 675.80, "l": 673.20, "c": 675.60, "v": 2150000},
        {"o": 675.60, "h": 677.00, "l": 674.40, "c": 676.85, "v": 1900000},
        {"o": 676.85, "h": 678.20, "l": 675.60, "c": 678.00, "v": 2250000},
        {"o": 678.00, "h": 679.40, "l": 677.80, "c": 679.15, "v": 2000000},
        {"o": 679.15, "h": 680.50, "l": 678.90, "c": 680.30, "v": 2100000},
        {"o": 680.30, "h": 681.70, "l": 679.00, "c": 681.50, "v": 1950000},
    ],
    "SNDK": [
        {"o": 1672.26, "h": 1685.00, "l": 1665.00, "c": 1678.50, "v": 2800000},
        {"o": 1678.50, "h": 1710.00, "l": 1675.00, "c": 1705.20, "v": 3100000},
        {"o": 1705.20, "h": 1750.00, "l": 1700.00, "c": 1740.80, "v": 3500000},
        {"o": 1740.80, "h": 1790.00, "l": 1735.00, "c": 1785.30, "v": 3800000},
        {"o": 1785.30, "h": 1820.00, "l": 1775.00, "c": 1810.50, "v": 4200000},
        {"o": 1810.50, "h": 1850.00, "l": 1805.00, "c": 1842.70, "v": 4400000},
        {"o": 1842.70, "h": 1870.00, "l": 1835.00, "c": 1865.90, "v": 4600000},
        {"o": 1865.90, "h": 1885.00, "l": 1855.00, "c": 1875.40, "v": 4300000},
        {"o": 1875.40, "h": 1895.00, "l": 1868.00, "c": 1888.60, "v": 4500000},
        {"o": 1888.60, "h": 1900.00, "l": 1875.00, "c": 1881.51, "v": 4800000},
    ],
    "NOK": [
        {"o": 13.57, "h": 13.70, "l": 13.40, "c": 13.62, "v": 18000000},
        {"o": 13.62, "h": 13.78, "l": 13.55, "c": 13.72, "v": 19500000},
        {"o": 13.72, "h": 13.85, "l": 13.65, "c": 13.80, "v": 21000000},
        {"o": 13.80, "h": 13.90, "l": 13.72, "c": 13.85, "v": 20500000},
        {"o": 13.85, "h": 13.95, "l": 13.78, "c": 13.90, "v": 22000000},
        {"o": 13.90, "h": 14.00, "l": 13.82, "c": 13.95, "v": 21500000},
        {"o": 13.95, "h": 14.10, "l": 13.88, "c": 14.05, "v": 23000000},
        {"o": 14.05, "h": 14.15, "l": 13.95, "c": 14.09, "v": 22500000},
        {"o": 14.09, "h": 14.17, "l": 14.00, "c": 14.12, "v": 21000000},
        {"o": 14.12, "h": 14.20, "l": 14.05, "c": 14.09, "v": 20000000},
    ],
    "SQQQ": [
        {"o": 44.19, "h": 45.01, "l": 43.50, "c": 43.80, "v": 25000000},
        {"o": 43.80, "h": 44.50, "l": 43.20, "c": 44.00, "v": 26500000},
        {"o": 44.00, "h": 44.80, "l": 43.00, "c": 43.50, "v": 28000000},
        {"o": 43.50, "h": 44.00, "l": 42.50, "c": 42.80, "v": 29500000},
        {"o": 42.80, "h": 43.20, "l": 42.00, "c": 42.30, "v": 31000000},
        {"o": 42.30, "h": 42.80, "l": 41.50, "c": 41.70, "v": 33000000},
        {"o": 41.70, "h": 42.00, "l": 41.00, "c": 41.20, "v": 35000000},
        {"o": 41.20, "h": 41.50, "l": 40.44, "c": 40.65, "v": 37000000},
        {"o": 40.65, "h": 41.10, "l": 40.44, "c": 40.80, "v": 36000000},
        {"o": 40.80, "h": 41.00, "l": 40.44, "c": 40.83, "v": 34000000},
    ],
}

SIGNALS = {
    "MU": [
        {"id": 1, "strategy_type": "ma_trend", "direction": "bullish",
         "confidence": 0.72, "strength": 0.65,
         "explanation": "50-day SMA ($950.40) > 200-day SMA ($702.15) — strong uptrend confirmed",
         "generated_at": (datetime.utcnow().replace(microsecond=0) - timedelta(hours=2)).isoformat() + "Z"},
        {"id": 2, "strategy_type": "volume_breakout", "direction": "bullish",
         "confidence": 0.65, "strength": 0.70,
         "explanation": "Volume spike (+22%) on price breakout above $970 support",
         "generated_at": (datetime.utcnow().replace(microsecond=0) - timedelta(hours=4)).isoformat() + "Z"},
    ],
    "VOO": [
        {"id": 3, "strategy_type": "ma_trend", "direction": "bullish",
         "confidence": 0.58, "strength": 0.55,
         "explanation": "50-day SMA ($668.20) > 200-day SMA ($640.45) — uptrend detected",
         "generated_at": (datetime.utcnow().replace(microsecond=0) - timedelta(hours=3)).isoformat() + "Z"},
    ],
    "SNDK": [
        {"id": 4, "strategy_type": "ma_trend", "direction": "bullish",
         "confidence": 0.81, "strength": 0.78,
         "explanation": "50-day SMA ($1,450) > 200-day SMA ($720) — strong uptrend after spin-off",
         "generated_at": (datetime.utcnow().replace(microsecond=0) - timedelta(hours=1)).isoformat() + "Z"},
    ],
    "NOK": [
        {"id": 5, "strategy_type": "ma_trend", "direction": "bullish",
         "confidence": 0.62, "strength": 0.58,
         "explanation": "50-day SMA ($12.80) > 200-day SMA ($9.50) — uptrend on AI network demand",
         "generated_at": (datetime.utcnow().replace(microsecond=0) - timedelta(hours=3)).isoformat() + "Z"},
    ],
    "SQQQ": [
        {"id": 6, "strategy_type": "ma_trend", "direction": "bearish",
         "confidence": 0.45, "strength": 0.40,
         "explanation": "50-day SMA ($55.20) < 200-day SMA ($72.30) — bearish as tech rallies",
         "generated_at": (datetime.utcnow().replace(microsecond=0) - timedelta(hours=4)).isoformat() + "Z"},
    ],
}

NEWS_ARTICLES = [
    {"id": 1, "ticker": "MU",
     "title": "Micron beats Q3 earnings estimates on strong AI demand",
     "source": "Reuters", "event_type": "earnings_beat",
     "published_utc": (datetime.utcnow() - timedelta(hours=5)).isoformat() + "Z",
     "score": {"final": 85.0, "explanation": "Strong earnings beat on AI-driven memory demand"}},
    {"id": 2, "ticker": "MU",
     "title": "Micron announces new HBM4 memory technology partnership",
     "source": "Bloomberg", "event_type": "analyst_upgrade",
     "published_utc": (datetime.utcnow() - timedelta(hours=12)).isoformat() + "Z",
     "score": {"final": 65.0, "explanation": "Bullish signal from next-gen memory technology"}},
    {"id": 3, "ticker": "VOO",
     "title": "VOO sees record inflows as investors rotate to passive funds",
     "source": "MarketWatch", "event_type": "general_positive",
     "published_utc": (datetime.utcnow() - timedelta(hours=8)).isoformat() + "Z",
     "score": {"final": 35.0, "explanation": "Positive sentiment from increased passive fund flows"}},
    {"id": 4, "ticker": "VOO",
     "title": "S&P 500 faces headwinds from persistent inflation data",
     "source": "Financial Times", "event_type": "macro_negative",
     "published_utc": (datetime.utcnow() - timedelta(hours=18)).isoformat() + "Z",
     "score": {"final": -45.0, "explanation": "Inflation concerns weighing on broad market indices"}},
    {"id": 5, "ticker": "MU",
     "title": "Semiconductor sector rally lifts Micron shares",
     "source": "CNBC", "event_type": "sector_positive",
     "published_utc": (datetime.utcnow() - timedelta(hours=3)).isoformat() + "Z",
     "score": {"final": 55.0, "explanation": "Broad semiconductor sector strength driving gains"}},
]

WATCHLIST = ["MU", "VOO", "SNDK", "NOK", "SQQQ"]

HEALTH_WARNINGS: list = []


# ── Helpers ────────────────────────────────────────────────────────────────

def _now_utc():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _price_for(ticker: str):
    return PRICES.get(ticker.upper())

def _signal_for(ticker: str):
    sigs = SIGNALS.get(ticker.upper(), [])
    return sigs[0] if sigs else None

def _health_for(ticker: str):
    return {"status": "healthy", "warning_type": None, "message": "Data is current",
            "checked_at": _now_utc(), "provider": "Polygon.io"}

def _news_for(ticker: str):
    return [a for a in NEWS_ARTICLES if a["ticker"] == ticker.upper()]

def _to_obj(d: dict):
    """Recursively convert a dict to SimpleNamespace for _build_decision_summary."""
    if isinstance(d, dict):
        return SimpleNamespace(**{k: _to_obj(v) for k, v in d.items()})
    if isinstance(d, list):
        return [_to_obj(i) for i in d]
    return d


# ── Routes ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info("Signal Desk demo server starting...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Signal Desk demo server shutting down...")


@app.get("/")
async def root():
    return {
        "service": "Signal Desk Demo Server", "status": "running",
        "note": "Full API mock — open /docs for interactive docs.",
        "api_docs": "/docs",
        "frontend": "http://localhost:3000",
    }

@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "signal-desk-demo", "mode": "demo"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "tickers": len(TICKERS),
        "provider": {"name": "Polygon.io", "status": "connected", "latency_ms": 42},
    }


# ── Tickers ────────────────────────────────────────────────────────────────

@app.get("/api/v1/tickers")
async def list_tickers(active_only: bool = True):
    items = [v for v in TICKERS.values() if not active_only or v["is_active"]]
    return {"items": items, "total": len(items)}

@app.get("/api/v1/tickers/{ticker}")
async def get_ticker(ticker: str):
    t = TICKERS.get(ticker.upper())
    if not t:
        raise HTTPException(404, f"Ticker {ticker} not found")
    return t

@app.get("/api/v1/tickers/{ticker}/price")
async def get_price(ticker: str):
    t = ticker.upper()
    p = _price_for(t)
    sig = _signal_for(t)
    h = _health_for(t)
    now = _now_utc()
    return {
        "ticker": t,
        "price": p["price"] if p else None,
        "open": p["open"] if p else None,
        "high": p["high"] if p else None,
        "low": p["low"] if p else None,
        "volume": p["volume"] if p else 0,
        "bid": p["bid"] if p else None,
        "ask": p["ask"] if p else None,
        "session": p["session"] if p else "NONE",
        "updated_utc": now, "updated_et": now,
        "provider": p["provider"] if p else "Polygon.io",
        "signal": {
            "direction": sig["direction"] if sig else "neutral",
            "confidence": sig["confidence"] if sig else 0,
            "strategy": sig["strategy_type"] if sig else None,
        } if sig else None,
        "health": {
            "status": h["status"], "warning": h["warning_type"],
            "message": h["message"],
        },
    }

@app.get("/api/v1/tickers/{ticker}/bars")
async def get_bars(ticker: str, start: str = None, end: str = None,
                   timespan: str = "minute", limit: int = 100):
    t = ticker.upper()
    bars_data = BARS.get(t, [])
    base_time = datetime.utcnow().replace(microsecond=0)
    items = []
    for i, b in enumerate(bars_data):
        ts = (base_time - timedelta(minutes=len(bars_data) - i)).isoformat() + "Z"
        items.append({
            "timestamp_utc": ts, "timestamp_et": ts, "session": "REGULAR",
            "open": b["o"], "high": b["h"], "low": b["l"],
            "close": b["c"], "volume": b["v"],
        })
    return {"ticker": t, "count": len(items), "items": items[-limit:]}

@app.get("/api/v1/tickers/{ticker}/signals")
async def get_ticker_signals(ticker: str, limit: int = 20):
    t = ticker.upper()
    sigs = SIGNALS.get(t, [])
    return {"ticker": t, "count": len(sigs), "items": sigs[:limit]}

@app.get("/api/v1/tickers/{ticker}/health")
async def get_ticker_health(ticker: str):
    t = ticker.upper()
    h = _health_for(t)
    return {"ticker": t, **h}

@app.post("/api/v1/tickers/{ticker}/refresh")
async def refresh_ticker(ticker: str):
    logger.info("refresh requested for %s", ticker)
    return {
        "ticker": ticker.upper(), "signal_generated": True,
        "signal_direction": "bullish",
        "message": f"Refreshed data and MA trend signal for {ticker.upper()}",
    }

@app.get("/api/v1/tickers/{ticker}/verification")
async def verification(ticker: str):
    logger.info("verification requested for %s", ticker)
    return get_verification_config(ticker.upper())

@app.get("/api/v1/tickers/{ticker}/decision-summary")
async def decision_summary(ticker: str):
    logger.info("decision-summary requested for %s", ticker)
    t = ticker.upper()
    p = _price_for(t)
    s = _signal_for(t)
    h = _health_for(t)
    news_articles = []
    for a in _news_for(t):
        news_articles.append(SimpleNamespace(
            scored_news=SimpleNamespace(final_score=a["score"]["final"])
        ))
    signal_obj = _to_obj(s) if s else None
    health_obj = _to_obj(h)
    return _build_decision_summary(
        ticker=t,
        quote=p,
        signal_obj=signal_obj,
        health=health_obj,
        news_articles=news_articles,
    )


# ── Dashboard ──────────────────────────────────────────────────────────────

@app.get("/api/v1/dashboard")
async def dashboard():
    items = []
    for sym in WATCHLIST:
        p = PRICES.get(sym)
        h = _health_for(sym)
        items.append({
            "ticker": sym,
            "price": p["price"] if p else None,
            "session": p["session"] if p else "NONE",
            "health_status": h["status"],
        })
    return {
        "market_hours": "Market Open — Regular Session (09:30–16:00 ET)",
        "last_updated": _now_utc(),
        "watchlist": {"items": items},
    }


# ── Watchlist ──────────────────────────────────────────────────────────────

@app.get("/api/v1/dashboard/watchlist")
async def get_watchlist():
    items = []
    for sym in WATCHLIST:
        t = TICKERS.get(sym)
        p = PRICES.get(sym)
        h = _health_for(sym)
        s = _signal_for(sym)
        now = _now_utc()
        items.append({
            "ticker": sym,
            "name": t["name"] if t else sym,
            "price": p["price"] if p else None,
            "previous_close": p.get("previous_close") if p else None,
            "session": p["session"] if p else "NONE",
            "signal_direction": s["direction"] if s else "neutral",
            "health_status": h["status"],
            "updated_et": now,
        })
    return {"items": items}

@app.post("/api/v1/dashboard/watchlist/{ticker}")
async def add_to_watchlist(ticker: str):
    t = ticker.upper()
    if t not in WATCHLIST:
        WATCHLIST.append(t)
    logger.info("added %s to watchlist", t)
    return {"status": "ok", "ticker": t}

@app.delete("/api/v1/dashboard/watchlist/{ticker}")
async def remove_from_watchlist(ticker: str):
    t = ticker.upper()
    if t in WATCHLIST:
        WATCHLIST.remove(t)
    logger.info("removed %s from watchlist", t)
    return {"status": "ok", "ticker": t}


# ── News ───────────────────────────────────────────────────────────────────

@app.get("/api/v1/news")
async def get_news(ticker: str = None):
    items = NEWS_ARTICLES
    if ticker:
        items = _news_for(ticker)
    return {"items": items, "total": len(items)}

@app.post("/api/v1/news/ingest")
async def ingest_news(ticker: str = None):
    logger.info("news ingest requested (stub) ticker=%s", ticker)
    return {"status": "ok", "message": "News ingestion triggered (demo stub)", "articles_ingested": 3}

@app.post("/api/v1/news")
async def post_news():
    return {"status": "ok", "message": "News article stored (demo stub)"}

@app.get("/api/v1/news/{news_id}")
async def get_news_detail(news_id: int):
    for a in NEWS_ARTICLES:
        if a["id"] == news_id:
            return a
    raise HTTPException(404, "News article not found")


# ── Signals ────────────────────────────────────────────────────────────────

@app.get("/api/v1/signals")
async def get_signals(ticker: str = None):
    if ticker:
        return {"items": SIGNALS.get(ticker.upper(), [])}
    all_sigs = []
    for sym, sigs in SIGNALS.items():
        all_sigs.extend(sigs)
    return {"items": all_sigs}

@app.get("/api/v1/health/data")
async def health_data():
    return {"items": HEALTH_WARNINGS}

@app.get("/api/v1/health")
async def api_health():
    return await health()


# ── Activity Log ───────────────────────────────────────────────────────────

ACTIVITY_LOG = [
    {"id": 1, "timestamp": (datetime.utcnow() - timedelta(seconds=30)).isoformat() + "Z",
     "level": "INFO", "action": "auto_refresh_started", "ticker": None,
     "message": "Auto refresh cycle started", "duration_ms": None},
    {"id": 2, "timestamp": (datetime.utcnow() - timedelta(seconds=28)).isoformat() + "Z",
     "level": "INFO", "action": "price_fetched", "ticker": "MU",
     "message": "MU price: 977.18", "duration_ms": 1200},
    {"id": 3, "timestamp": (datetime.utcnow() - timedelta(seconds=25)).isoformat() + "Z",
     "level": "INFO", "action": "price_fetched", "ticker": "VOO",
     "message": "VOO price: 678.35", "duration_ms": 1100},
    {"id": 4, "timestamp": (datetime.utcnow() - timedelta(seconds=22)).isoformat() + "Z",
     "level": "INFO", "action": "signal_generated", "ticker": "MU",
     "message": "Short-Term Bullish signal generated", "duration_ms": None},
    {"id": 5, "timestamp": (datetime.utcnow() - timedelta(seconds=20)).isoformat() + "Z",
     "level": "INFO", "action": "auto_refresh_completed", "ticker": None,
     "message": "Auto refresh cycle completed", "duration_ms": 10000},
    {"id": 6, "timestamp": (datetime.utcnow() - timedelta(minutes=2)).isoformat() + "Z",
     "level": "WARNING", "action": "data_health_warning", "ticker": "SNDK",
     "message": "SNDK: no recent data", "duration_ms": None},
]

LOG_ID = 7


@app.get("/api/v1/activity-log")
async def get_activity_log(limit: int = 100, offset: int = 0, action: str = None,
                            ticker: str = None, level: str = None):
    items = list(ACTIVITY_LOG)
    if action:
        items = [i for i in items if i["action"] == action]
    if ticker:
        items = [i for i in items if i["ticker"] == ticker]
    if level:
        items = [i for i in items if i["level"] == level]
    items.sort(key=lambda x: x["id"], reverse=True)
    return {"items": items[offset:offset + limit], "total": len(items)}


# ── Backtest ──────────────────────────────────────────────────────────────

BACKTEST_RUNS = []


@app.post("/api/v1/backtest/run")
async def run_backtest(ticker: str = "MU", strategy: str = "momentum_5m",
                        start_date: str = None, end_date: str = None):
    global LOG_ID
    run_id = len(BACKTEST_RUNS) + 1
    result = {
        "run_id": run_id,
        "strategy": strategy,
        "ticker": ticker.upper(),
        "bars_used": 4500,
        "start": start_date or "2026-03-12T00:00:00",
        "end": end_date or "2026-06-12T23:59:59",
        "total_return_pct": 3.42,
        "num_trades": 28,
        "win_rate": 0.6071,
        "avg_win": 1.85,
        "avg_loss": -1.12,
        "profit_factor": 2.34,
        "max_drawdown_pct": 4.21,
        "avg_holding_bars": 7.3,
        "largest_loss": -3.45,
        "trade_log": [],
        "slippage_assumption": 0.001,
        "fee_assumption": 0.001,
    }
    BACKTEST_RUNS.append({"run_id": run_id, "strategy": strategy, "status": "completed",
                          "created_at": datetime.utcnow().isoformat() + "Z"})
    ACTIVITY_LOG.insert(0, {"id": LOG_ID, "timestamp": datetime.utcnow().isoformat() + "Z",
                            "level": "INFO", "action": "backtest_completed", "ticker": ticker,
                            "message": f"Backtest {strategy} completed: +{result['total_return_pct']}%",
                            "duration_ms": None})
    LOG_ID += 1
    return result


@app.get("/api/v1/backtest/runs")
async def list_backtest_runs(limit: int = 20):
    return {"items": list(reversed(BACKTEST_RUNS))}


@app.get("/api/v1/backtest/runs/{run_id}")
async def get_backtest_run(run_id: int):
    for r in BACKTEST_RUNS:
        if r["run_id"] == run_id:
            return r
    raise HTTPException(404, "Backtest run not found")


# ── Data Confidence ───────────────────────────────────────────────────────

DATA_CONFIDENCE = {
    "MU": {"score": 91, "label": "Healthy", "breakdown": []},
    "VOO": {"score": 88, "label": "Healthy", "breakdown": [{"reason": "stale_data", "penalty": 12}]},
    "SNDK": {"score": 22, "label": "Unreliable",
             "breakdown": [{"reason": "missing_data", "penalty": 30},
                           {"reason": "stale_data", "penalty": 20},
                           {"reason": "low_liquidity", "penalty": 15}]},
}


@app.get("/api/v1/data-confidence/{ticker}")
async def get_data_confidence(ticker: str):
    return DATA_CONFIDENCE.get(ticker.upper(), {"score": 0, "label": "No Data", "breakdown": []})


# ── Short-Term Indicators ─────────────────────────────────────────────────

@app.get("/api/v1/indicators/{ticker}")
async def get_indicators(ticker: str):
    mock = {
        "MU": {
            "ticker": "MU", "bars_available": 180, "current_price": 977.18,
            "current_volume": 56337333,
            "change_1m_pct": 0.12, "change_5m_pct": 0.45, "change_10m_pct": 0.89,
            "vwap": 974.50, "vwap_distance_pct": 0.28,
            "volume_spike_5m_pct": 22.5,
            "short_term_direction": "Short-Term Bullish",
        },
        "VOO": {
            "ticker": "VOO", "bars_available": 180, "current_price": 678.35,
            "current_volume": 7071988,
            "change_1m_pct": -0.05, "change_5m_pct": 0.15, "change_10m_pct": 0.32,
            "vwap": 677.80, "vwap_distance_pct": 0.08,
            "volume_spike_5m_pct": -12.0,
            "short_term_direction": "Neutral",
        },
        "SNDK": {
            "ticker": "SNDK", "bars_available": 0, "status": "insufficient_data",
        },
    }
    result = mock.get(ticker.upper(), {"error": "Ticker not found"})
    return result


# ── Scheduler Status ──────────────────────────────────────────────────────

@app.get("/api/v1/scheduler/status")
async def scheduler_status():
    return {
        "is_running": True,
        "in_progress": False,
        "last_refresh": datetime.utcnow().isoformat() + "Z",
        "seconds_until_next": 42,
        "interval_seconds": 60,
    }


# ── Retention ─────────────────────────────────────────────────────────────

@app.post("/api/v1/retention/cleanup")
async def retention_cleanup():
    return {
        "cutoff": (datetime.utcnow() - timedelta(days=120)).isoformat() + "Z",
        "deleted": {
            "price_bars": 15234,
            "price_bars_1m_clean": 15234,
            "quote_snapshots": 15234,
            "activity_logs": 890,
        },
    }


# ── Methodology ───────────────────────────────────────────────────────────

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


@app.get("/api/v1/methodologies")
async def list_methodologies():
    return {"items": METHODOLOGIES}


@app.get("/api/v1/methodologies/{name}")
async def get_methodology(name: str):
    for m in METHODOLOGIES:
        if m["name"].lower() == name.lower():
            return m
    raise HTTPException(404, "Methodology not found")


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
