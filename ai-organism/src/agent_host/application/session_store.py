from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time
import asyncio
import os


def make_session_key(*, tenant_id: Optional[str], session_id: str) -> str:
    """Avoid cross-tenant collisions."""
    t = (tenant_id or "public").strip() or "public"
    return f"{t}:{session_id}"


class SessionStore(ABC):
    @abstractmethod
    async def get(self, session_id: str) -> Dict[str, Any]: ...

    @abstractmethod
    async def set(self, session_id: str, data: Dict[str, Any]) -> None: ...


class InMemoryTTLSessionStore(SessionStore):
    """
    Store opcional para agentes que precisam guardar estado por sessão.
    Idealmente, a maioria dos agentes deve ser stateless.
    """
    def __init__(self, ttl_s: int = 1800):
        self._ttl_s = ttl_s
        self._data: Dict[str, tuple[float, Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def get(self, session_id: str) -> Dict[str, Any]:
        now = time.time()
        async with self._lock:
            item = self._data.get(session_id)
            if not item:
                return {}
            ts, payload = item
            if now - ts > self._ttl_s:
                self._data.pop(session_id, None)
                return {}
            return dict(payload)

    async def set(self, session_id: str, data: Dict[str, Any]) -> None:
        async with self._lock:
            self._data[session_id] = (time.time(), dict(data))


class RedisSessionStore(SessionStore):
    """Redis-backed session store (optional).

    Enable with:
      SESSION_STORE=redis
      REDIS_URL=redis://localhost:6379/0
    """

    def __init__(self, *, redis_url: str, ttl_s: int = 1800):
        try:
            import redis.asyncio as redis  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "RedisSessionStore requires 'redis' package. Install it or use in-memory store."
            ) from e

        self._redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self._ttl_s = ttl_s

    async def get(self, session_id: str) -> Dict[str, Any]:
        import json

        raw = await self._redis.get(session_id)
        if not raw:
            return {}
        try:
            obj = json.loads(raw)
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}

    async def set(self, session_id: str, data: Dict[str, Any]) -> None:
        import json

        await self._redis.set(session_id, json.dumps(dict(data), ensure_ascii=False), ex=self._ttl_s)


def build_session_store_from_env() -> SessionStore:
    """Factory used by the host."""
    ttl_s = int(os.getenv("SESSION_TTL_S", "1800"))
    kind = os.getenv("SESSION_STORE", "memory").strip().lower()
    if kind == "redis":
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            raise ValueError("SESSION_STORE=redis requires REDIS_URL")
        return RedisSessionStore(redis_url=redis_url, ttl_s=ttl_s)
    return InMemoryTTLSessionStore(ttl_s=ttl_s)