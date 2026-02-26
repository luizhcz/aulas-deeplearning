from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict
import time
import asyncio

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