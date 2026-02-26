from __future__ import annotations
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from registry_service.infrastructure.repo_inmemory import InMemoryRegistryRepo
from registry_service.application.service import RegistryService

app = FastAPI(title="Agent Registry", version="1.0.0")
svc = RegistryService(InMemoryRegistryRepo())

class HeartbeatRequest(BaseModel):
    name: str
    version: str
    base_url: str
    meta: Dict[str, Any] = {}

@app.post("/heartbeat")
def heartbeat(req: HeartbeatRequest):
    svc.heartbeat(req.name, req.version, req.base_url, req.meta)
    return {"ok": True}

@app.get("/agents")
def list_agents(name: Optional[str] = None):
    items = svc.list(name=name)
    return [i.model_dump() for i in items]