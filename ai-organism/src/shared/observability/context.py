from __future__ import annotations

"""Lightweight request context propagation (dependency-free).

Context values are attached to logs/metrics/audit.
"""

from contextvars import ContextVar
from typing import Optional


request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
agent_name_var: ContextVar[Optional[str]] = ContextVar("agent_name", default=None)


def set_context(
    *,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    agent_name: Optional[str] = None,
) -> None:
    if request_id is not None:
        request_id_var.set(request_id)
    if trace_id is not None:
        trace_id_var.set(trace_id)
    if session_id is not None:
        session_id_var.set(session_id)
    if tenant_id is not None:
        tenant_id_var.set(tenant_id)
    if user_id is not None:
        user_id_var.set(user_id)
    if agent_name is not None:
        agent_name_var.set(agent_name)


def clear_context() -> None:
    request_id_var.set(None)
    trace_id_var.set(None)
    session_id_var.set(None)
    tenant_id_var.set(None)
    user_id_var.set(None)
    agent_name_var.set(None)