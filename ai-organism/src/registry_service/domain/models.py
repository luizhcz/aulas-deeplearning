from __future__ import annotations
from pydantic import BaseModel
from typing import Dict, Any

class AgentInstance(BaseModel):
    name: str
    version: str
    base_url: str
    status: str = "UP"
    last_heartbeat_ts: float
    meta: Dict[str, Any] = {}