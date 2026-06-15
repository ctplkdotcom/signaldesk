from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models import ActivityLog
from app.config import settings


class ActivityLogService:
    async def log(
        self,
        action: str,
        level: str = "INFO",
        ticker: str | None = None,
        message: str | None = None,
        details: dict | None = None,
        duration_ms: int | None = None,
    ) -> ActivityLog:
        async with async_session_factory() as session:
            entry = ActivityLog(
                action=action,
                level=level,
                ticker=ticker,
                message=message,
                details=details,
                duration_ms=duration_ms,
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            return entry

    async def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        action: str | None = None,
        ticker: str | None = None,
        level: str | None = None,
    ) -> list[ActivityLog]:
        async with async_session_factory() as session:
            stmt = select(ActivityLog).order_by(desc(ActivityLog.timestamp))
            if action:
                stmt = stmt.where(ActivityLog.action == action)
            if ticker:
                stmt = stmt.where(ActivityLog.ticker == ticker)
            if level:
                stmt = stmt.where(ActivityLog.level == level)
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def cleanup_old(self) -> int:
        cutoff = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        async with async_session_factory() as session:
            stmt = delete(ActivityLog).where(
                ActivityLog.timestamp < cutoff
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount or 0

    async def timed(self, action: str, ticker: str | None = None, **kwargs):
        def decorator(func):
            async def wrapper(*args, **kw):
                start = time.monotonic()
                try:
                    result = await func(*args, **kw)
                    duration = int((time.monotonic() - start) * 1000)
                    await self.log(
                        action=action,
                        level="INFO",
                        ticker=ticker,
                        message=f"{action} completed",
                        duration_ms=duration,
                        details=kwargs.get("details"),
                    )
                    return result
                except Exception as e:
                    duration = int((time.monotonic() - start) * 1000)
                    await self.log(
                        action=f"{action}_failed",
                        level="ERROR",
                        ticker=ticker,
                        message=str(e),
                        duration_ms=duration,
                    )
                    raise

            return wrapper

        return decorator
