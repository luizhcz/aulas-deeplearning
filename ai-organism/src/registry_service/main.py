from __future__ import annotations
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from shared.observability.fastapi import instrument_fastapi
from shared.observability.audit import audit_event
from shared.observability.context import set_context
from shared.observability.logging import get_logger

from registry_service.infrastructure.repo_inmemory import InMemoryRegistryRepo
from registry_service.application.service import RegistryService

app = FastAPI(title="Agent Registry", version="1.0.0")
instrument_fastapi(app, service_name="registry")
svc = RegistryService(InMemoryRegistryRepo())
log = get_logger("registry")

class HeartbeatRequest(BaseModel):
    name: str
    version: str
    base_url: str
    meta: Dict[str, Any] = {}

@app.post("/heartbeat")
def heartbeat(req: HeartbeatRequest):
    set_context(agent_name=req.name, trace_id=None)
    svc.heartbeat(req.name, req.version, req.base_url, req.meta)

    audit_event(
        event="registry.heartbeat",
        action="upsert",
        outcome="success",
        subject={"agent": req.name, "version": req.version},
        object_={"base_url": req.base_url},
        request={"meta": req.meta},
    )
    return {"ok": True}

@app.get("/agents")
def list_agents(name: Optional[str] = None):
    items = svc.list(name=name)
    return [i.model_dump() for i in items]