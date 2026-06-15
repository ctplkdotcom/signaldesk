from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from app.config import settings


class CacheClient:
    def __init__(self):
        self._redis: aioredis.Redis | None = None
        self._default_ttl = 60

    async def get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        return self._redis

    async def get(self, key: str) -> Any | None:
        r = await self.get_redis()
        val = await r.get(key)
        if val is not None:
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return val
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        r = await self.get_redis()
        ttl = ttl or self._default_ttl
        await r.setex(key, ttl, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        r = await self.get_redis()
        await r.delete(key)

    async def exists(self, key: str) -> bool:
        r = await self.get_redis()
        return await r.exists(key) > 0

    async def clear_pattern(self, pattern: str) -> None:
        r = await self.get_redis()
        cursor = 0
        while True:
            cursor, keys = await r.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await r.delete(*keys)
            if cursor == 0:
                break

    async def close(self):
        if self._redis:
            await self._redis.aclose()
            self._redis = None


cache = CacheClient()
