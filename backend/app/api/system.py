from fastapi import APIRouter, HTTPException, Query

from app.services.activity_log import ActivityLogService
from app.services.backtest_service import BacktestService
from app.services.retention_service import RetentionService
from app.services.data_confidence import DataConfidenceService
from app.services.short_term_indicators import ShortTermIndicatorService
from app.services.scheduler import scheduler
from app.models import Methodology
from app.database import async_session_factory
from sqlalchemy import select

router = APIRouter()
activity_log = ActivityLogService()
backtest = BacktestService()
retention = RetentionService()
data_confidence = DataConfidenceService()
short_term = ShortTermIndicatorService()


# ── Activity Log ──────────────────────────────────────────────────────────

@router.get("/activity-log")
async def get_activity_log(
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    action: str | None = Query(None),
    ticker: str | None = Query(None),
    level: str | None = Query(None),
):
    logs = await activity_log.get_logs(
        limit=limit, offset=offset, action=action, ticker=ticker, level=level
    )
    return {
        "items": [
            {
                "id": log.id,
                "timestamp": str(log.timestamp),
                "level": log.level,
                "action": log.action,
                "ticker": log.ticker,
                "message": log.message,
                "duration_ms": log.duration_ms,
            }
            for log in logs
        ],
        "total": len(logs),
    }


# ── Backtest ─────────────────────────────────────────────────────────────

@router.post("/backtest/run")
async def run_backtest(
    ticker: str = Query(...),
    strategy: str = Query("momentum_5m"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
):
    from datetime import datetime
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    result = await backtest.run_backtest(
        ticker=ticker, strategy=strategy, start_date=start, end_date=end
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/backtest/runs")
async def list_backtest_runs(limit: int = Query(20, le=100)):
    return {"items": await backtest.list_runs(limit=limit)}


@router.get("/backtest/runs/{run_id}")
async def get_backtest_run(run_id: int):
    result = await backtest.get_results(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return result


# ── Data Confidence ───────────────────────────────────────────────────────

@router.get("/data-confidence/{ticker}")
async def get_ticker_data_confidence(ticker: str):
    return await data_confidence.get_confidence(ticker)


# ── Short-Term Indicators ────────────────────────────────────────────────

@router.get("/indicators/{ticker}")
async def get_short_term_indicators(ticker: str):
    result = await short_term.get_indicators(ticker)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Retention ────────────────────────────────────────────────────────────

@router.post("/retention/cleanup")
async def run_retention_cleanup():
    result = await retention.cleanup()
    return result


# ── Scheduler ────────────────────────────────────────────────────────────

@router.get("/scheduler/status")
async def get_scheduler_status():
    return {
        "is_running": scheduler.is_running,
        "in_progress": scheduler.in_progress,
        "last_refresh": scheduler.last_refresh,
        "seconds_until_next": scheduler.seconds_until_next,
        "interval_seconds": 60,
    }


@router.post("/scheduler/refresh")
async def manual_refresh(ticker: str | None = Query(None)):
    result = await scheduler.refresh_now(ticker)
    return result


# ── Methodologies ────────────────────────────────────────────────────────

@router.get("/methodologies")
async def list_methodologies():
    async with async_session_factory() as session:
        result = await session.execute(
            select(Methodology).order_by(Methodology.name)
        )
        return {
            "items": [
                {
                    "name": m.name,
                    "version": m.version,
                    "description": m.description,
                    "input_data": m.input_data,
                    "formula": m.formula,
                    "assumptions": m.assumptions,
                    "limitations": m.limitations,
                }
                for m in result.scalars().all()
            ]
        }


@router.get("/methodologies/{name}")
async def get_methodology(name: str):
    async with async_session_factory() as session:
        result = await session.execute(
            select(Methodology).where(Methodology.name == name)
        )
        m = result.scalar_one_or_none()
        if not m:
            raise HTTPException(404, "Methodology not found")
        return {
            "name": m.name,
            "version": m.version,
            "description": m.description,
            "input_data": m.input_data,
            "formula": m.formula,
            "assumptions": m.assumptions,
            "limitations": m.limitations,
        }
