from fastapi import APIRouter, HTTPException

from app.services.reference_data import ReferenceDataService
from app.services.market_data import MarketDataService
from app.services.signal_engine import SignalEngine
from app.services.data_health import DataHealthService
from app.utils.time import get_market_hours_description, get_et_now

router = APIRouter()
ref_data = ReferenceDataService()
market_data = MarketDataService()
signal_engine = SignalEngine()
data_health = DataHealthService()


@router.get("")
async def get_dashboard():
    watchlist_items = await ref_data.get_watchlist()
    watchlist_data = []
    for item in watchlist_items:
        t = await ref_data.get_ticker_by_id(item.ticker_id)
        if not t:
            continue
        quote = await market_data.get_latest_quote(t.ticker)
        sig = await signal_engine.get_latest_signal(t.ticker)
        health = await data_health.get_ticker_health(t.ticker)

        watchlist_data.append({
            "ticker": t.ticker,
            "name": t.name or t.ticker,
            "price": quote.get("price") if quote else None,
            "session": quote.get("session") if quote else None,
            "signal_direction": sig.direction if sig else None,
            "signal_confidence": sig.confidence if sig else 0,
            "health_status": health.status if health else "unknown",
            "last_updated": quote.get("timestamp_et") if quote else None,
        })

    signals = await signal_engine.get_signals(limit=10)
    warnings = await data_health.get_all_health_warnings()

    return {
        "watchlist": {"items": watchlist_data, "count": len(watchlist_data)},
        "market_hours": get_market_hours_description(),
        "total_signals": len(signals),
        "health_warnings": warnings[:10],
        "last_updated": str(get_et_now()),
    }


@router.get("/watchlist")
async def get_watchlist():
    items = await ref_data.get_watchlist()
    result = []
    for item in items:
        t = await ref_data.get_ticker_by_id(item.ticker_id)
        if not t:
            continue
        quote = await market_data.get_latest_quote(t.ticker)
        sig = await signal_engine.get_latest_signal(t.ticker)
        result.append({
            "id": item.id,
            "ticker": t.ticker,
            "name": t.name or t.ticker,
            "price": quote.get("price") if quote else None,
            "session": quote.get("session") if quote else None,
            "signal_direction": sig.direction if sig else None,
            "signal_confidence": sig.confidence if sig else 0,
            "updated_et": quote.get("updated_et") if quote else None,
        })
    return {"items": result, "count": len(result)}


@router.post("/watchlist/{ticker}")
async def add_to_watchlist(ticker: str):
    item = await ref_data.add_to_watchlist(ticker.upper())
    if not item:
        raise HTTPException(status_code=400, detail=f"{ticker.upper()} already in watchlist or not found")
    return {"message": f"Added {ticker.upper()}", "ticker_id": item.ticker_id}


@router.delete("/watchlist/{ticker}")
async def remove_from_watchlist(ticker: str):
    ok = await ref_data.remove_from_watchlist(ticker.upper())
    if not ok:
        raise HTTPException(status_code=404, detail=f"{ticker.upper()} not in watchlist")
    return {"message": f"Removed {ticker.upper()}"}
