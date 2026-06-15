from fastapi import APIRouter, Query

from app.services.signal_engine import SignalEngine

router = APIRouter()
signal_engine = SignalEngine()


@router.get("")
async def list_signals(ticker: str | None = Query(None), limit: int = Query(50, le=200)):
    signals = await signal_engine.get_signals(ticker=ticker, limit=limit)
    return {
        "items": [
            {
                "id": s.id,
                "ticker_id": s.ticker_id,
                "strategy_type": s.strategy_type,
                "direction": s.direction,
                "confidence": s.confidence,
                "strength": s.strength,
                "explanation": s.explanation,
                "generated_at": str(s.generated_at),
            }
            for s in signals
        ],
        "total": len(signals),
    }


@router.get("/{signal_id}")
async def get_signal(signal_id: int):
    signals = await signal_engine.get_signals(limit=500)
    for s in signals:
        if s.id == signal_id:
            return {
                "id": s.id,
                "ticker_id": s.ticker_id,
                "strategy_type": s.strategy_type,
                "direction": s.direction,
                "confidence": s.confidence,
                "strength": s.strength,
                "explanation": s.explanation,
                "data_sources": s.data_sources,
                "generated_at": str(s.generated_at),
            }
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Signal not found")
