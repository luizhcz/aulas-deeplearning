from __future__ import annotations
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentInstance(BaseModel):
    name: str
    version: str
    base_url: str
    status: str = "UP"
    last_heartbeat_ts: float
    meta: Dict[str, Any] = Field(default_factory=dict)