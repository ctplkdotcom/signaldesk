from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from app.services.market_data import MarketDataService
from app.services.activity_log import ActivityLogService
from app.services.data_confidence import DataConfidenceService
from app.services.short_term_indicators import ShortTermIndicatorService
from app.services.reference_data import ReferenceDataService
from app.services.signal_engine import SignalEngine
from app.config import settings


class RefreshScheduler:
    """Auto-refresh scheduler that runs every 60 seconds."""

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._running = False
        self._last_refresh: datetime | None = None
        self._next_refresh: datetime | None = None
        self._current_ticker: str | None = None
        self._refresh_in_progress = False
        self._log = ActivityLogService()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def last_refresh(self) -> str | None:
        return str(self._last_refresh) if self._last_refresh else None

    @property
    def seconds_until_next(self) -> int:
        if not self._next_refresh:
            return 0
        remaining = int((self._next_refresh - datetime.now(timezone.utc)).total_seconds())
        return max(0, remaining)

    @property
    def in_progress(self) -> bool:
        return self._refresh_in_progress

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        await self._log.log("scheduler_started", level="INFO", message="Auto-refresh scheduler started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self._log.log("scheduler_stopped", level="INFO", message="Auto-refresh scheduler stopped")

    async def refresh_now(self, ticker: str | None = None) -> dict:
        if self._refresh_in_progress:
            await self._log.log(
                "refresh_blocked",
                level="INFO",
                message="Refresh already in progress",
                details={"requested_ticker": ticker},
            )
            return {"status": "blocked", "message": "Refresh already in progress"}

        self._refresh_in_progress = True
        start = time.monotonic()
        try:
            result = await self._do_refresh(ticker)
            duration = int((time.monotonic() - start) * 1000)
            self._last_refresh = datetime.now(timezone.utc)
            self._next_refresh = datetime.now(timezone.utc).replace(
                second=0, microsecond=0
            ) + __import__("datetime").timedelta(seconds=settings.auto_refresh_interval)
            await self._log.log(
                "manual_refresh_completed",
                level="INFO",
                ticker=ticker,
                message=f"Manual refresh completed for {ticker or 'all'}",
                duration_ms=duration,
            )
            return result
        finally:
            self._refresh_in_progress = False

    async def _loop(self):
        while self._running:
            try:
                if not self._refresh_in_progress:
                    self._refresh_in_progress = True
                    try:
                        await self._do_refresh(None)
                        self._last_refresh = datetime.now(timezone.utc)
                        self._next_refresh = datetime.now(timezone.utc).replace(
                            second=0, microsecond=0
                        ) + __import__("datetime").timedelta(seconds=settings.auto_refresh_interval)
                    finally:
                        self._refresh_in_progress = False
                await asyncio.sleep(settings.auto_refresh_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self._log.log(
                    "scheduler_error",
                    level="ERROR",
                    message=f"Scheduler error: {e}",
                )
                await asyncio.sleep(10)

    async def _do_refresh(self, ticker: str | None) -> dict:
        ref_data = ReferenceDataService()
        market_data = MarketDataService()
        signal_engine = SignalEngine()
        data_conf = DataConfidenceService()
        indicators = ShortTermIndicatorService()

        tickers_to_refresh = []
        if ticker:
            tickers_to_refresh = [ticker.upper()]
        else:
            watchlist = await ref_data.get_watchlist()
            tickers_to_refresh = [item.ticker for item in watchlist]

        results = {}
        for sym in tickers_to_refresh:
            try:
                start = time.monotonic()
                self._current_ticker = sym
                await self._log.log(
                    "auto_refresh_ticker",
                    level="INFO",
                    ticker=sym,
                    message=f"Refreshing {sym}",
                )
                quote = await market_data.get_latest_quote(sym)
                await self._log.log(
                    "price_fetched",
                    level="INFO",
                    ticker=sym,
                    message=f"Price: {quote.price if quote else 'N/A'}",
                )
                health = await signal_engine.get_latest_signal(sym)
                confidence = await data_conf.get_confidence(sym)
                ind = await indicators.get_indicators(sym)
                duration = int((time.monotonic() - start) * 1000)
                results[sym] = {"status": "ok", "duration_ms": duration}
            except Exception as e:
                results[sym] = {"status": "error", "error": str(e)}
                await self._log.log(
                    "refresh_failed",
                    level="ERROR",
                    ticker=sym,
                    message=str(e),
                )
            finally:
                self._current_ticker = None

        return {"refreshed": len(tickers_to_refresh), "results": results}


scheduler = RefreshScheduler()
