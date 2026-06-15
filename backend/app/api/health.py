from fastapi import APIRouter

from app.services.data_health import DataHealthService
from app.providers.polygon import PolygonProvider
from app.services.reference_data import ReferenceDataService

router = APIRouter()
data_health_service = DataHealthService()
ref_data = ReferenceDataService()


@router.get("")
async def system_health():
    polygon = PolygonProvider()
    provider_health = await polygon.check_health()
    ticker_count = len(await ref_data.list_tickers())
    warnings = await data_health_service.get_all_health_warnings()
    return {
        "status": "healthy" if provider_health.status.value == "healthy" else "degraded",
        "provider": {
            "name": provider_health.provider,
            "status": provider_health.status.value,
            "latency_ms": provider_health.latency_ms,
        },
        "tickers": ticker_count,
        "warnings": len(warnings),
        "version": "0.1.0",
    }


@router.get("/data")
async def data_health():
    warnings = await data_health_service.get_all_health_warnings()
    return {"items": warnings, "total": len(warnings)}


@router.post("/check/{ticker}")
async def check_ticker(ticker: str):
    health = await data_health_service.check_ticker_health(ticker.upper())
    return {
        "ticker": ticker.upper(),
        "status": health.status,
        "warning_type": health.warning_type,
        "message": health.message,
        "checked_at": str(health.checked_at),
    }
