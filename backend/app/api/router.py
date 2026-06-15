from fastapi import APIRouter

from app.api import tickers, news, signals, dashboard, health, system

router = APIRouter(prefix="/api/v1")

router.include_router(tickers.router, prefix="/tickers", tags=["Tickers"])
router.include_router(news.router, prefix="/news", tags=["News"])
router.include_router(signals.router, prefix="/signals", tags=["Signals"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(system.router, tags=["System"])
