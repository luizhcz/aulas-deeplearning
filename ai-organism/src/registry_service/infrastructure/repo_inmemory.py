from __future__ import annotations
import time
from typing import Dict, List, Optional
import threading
from registry_service.domain.models import AgentInstance

class InMemoryRegistryRepo:
    def __init__(self):
        self._items: Dict[str, AgentInstance] = {}
        self._lock = threading.Lock()

    def upsert(self, inst: AgentInstance) -> None:
        key = f"{inst.name}@{inst.base_url}"
        with self._lock:
            self._items[key] = inst

    def list(self, name: Optional[str] = None) -> List[AgentInstance]:
        with self._lock:
            out = list(self._items.values())
        if name:
            out = [x for x in out if x.name == name]
        return out

    def mark_stale(self, stale_after_s: int = 30) -> None:
        now = time.time()
        with self._lock:
            for key, inst in list(self._items.items()):
                if now - inst.last_heartbeat_ts > stale_after_s:
                    self._items[key] = inst.model_copy(update={"status": "DOWN"})