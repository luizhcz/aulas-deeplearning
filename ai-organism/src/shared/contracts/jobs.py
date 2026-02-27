from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class Job(BaseModel):
    id: str
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: str = "PENDING"
    created_at: Optional[float] = None