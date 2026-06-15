from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.api.router import router
from app.utils.logging import setup_logging, get_logger
from app.services.scheduler import scheduler
from app.services.retention_service import RetentionService

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_startup", version=settings.app_version)
    await init_db()
    await scheduler.start()
    yield
    logger.info("app_shutdown")
    await scheduler.stop()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "scheduler_running": scheduler.is_running,
        "last_refresh": scheduler.last_refresh,
        "next_refresh_in": scheduler.seconds_until_next,
        "refresh_in_progress": scheduler.in_progress,
    }
