from __future__ import annotations
import time
from typing import Optional, List
from registry_service.domain.models import AgentInstance
from registry_service.infrastructure.repo_inmemory import InMemoryRegistryRepo

class RegistryService:
    def __init__(self, repo: InMemoryRegistryRepo):
        self.repo = repo

    def heartbeat(self, name: str, version: str, base_url: str, meta: dict) -> None:
        inst = AgentInstance(
            name=name,
            version=version,
            base_url=base_url,
            status="UP",
            last_heartbeat_ts=time.time(),
            meta=meta or {},
        )
        self.repo.upsert(inst)

    def list(self, name: Optional[str] = None) -> List[AgentInstance]:
        self.repo.mark_stale(stale_after_s=45)
        return self.repo.list(name=name)