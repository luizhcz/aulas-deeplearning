from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class AgentContext(BaseModel):
    session_id: str
    tenant_id: Optional[str] = None
    trace_id: Optional[str] = None
    user_id: Optional[str] = None

    # ✅ NOVO: habilita debug detalhado no retorno
    verbose: bool = False

    vars: Dict[str, Any] = Field(default_factory=dict)

class AgentInvokeRequest(BaseModel):
    input: Dict[str, Any]
    context: AgentContext

class AgentError(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

class AgentInvokeResponse(BaseModel):
    ok: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[AgentError] = None
    meta: Dict[str, Any] = Field(default_factory=dict)