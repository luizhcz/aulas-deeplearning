from __future__ import annotations
from agents.base.contracts import BaseAgent
from agent_host.application.session_store import InMemoryTTLSessionStore
from agent_host.infrastructure.fastapi_host import create_agent_app

def build_agent_http_host(
    agent: BaseAgent,
    *,
    registry_url: str | None = None,
    agent_base_url: str | None = None,
    heartbeat_interval_s: int = 10,
):
    session_store = InMemoryTTLSessionStore(ttl_s=1800)
    return create_agent_app(
        agent=agent,
        session_store=session_store,
        registry_url=registry_url,
        agent_base_url=agent_base_url,
        heartbeat_interval_s=heartbeat_interval_s,
    )