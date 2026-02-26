from __future__ import annotations
from typing import Any, Dict, Optional, Literal
from pydantic import BaseModel, Field

JobStatus = Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED"]

class JobSubmitResponse(BaseModel):
    accepted: bool = True
    job_id: str
    meta: Dict[str, Any] = Field(default_factory=dict)

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    ok: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    meta: Dict[str, Any] = Field(default_factory=dict)