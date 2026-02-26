from __future__ import annotations
import os
import asyncio
import traceback
from typing import Optional

import httpx
from fastapi import FastAPI
from pydantic import ValidationError

from shared.contracts.http import AgentInvokeRequest, AgentInvokeResponse, AgentError
from shared.observability.logging import get_logger
from agents.base.contracts import BaseAgent
from agent_host.application.session_store import SessionStore


def create_agent_app(
    agent: BaseAgent,
    session_store: SessionStore,
    *,
    registry_url: Optional[str] = None,
    agent_base_url: Optional[str] = None,
    heartbeat_interval_s: int = 10,
) -> FastAPI:
    sp = agent.spec()
    log = get_logger(f"agent.{sp.name}")

    registry_url = registry_url or os.getenv("REGISTRY_URL")
    agent_base_url = agent_base_url or os.getenv("AGENT_BASE_URL")
    agent_name = os.getenv("AGENT_NAME", sp.name)
    agent_version = os.getenv("AGENT_VERSION", sp.version)

    stop_event = asyncio.Event()
    heartbeat_task: Optional[asyncio.Task] = None

    async def _heartbeat_loop():
        if not (registry_url and agent_base_url):
            log.info("heartbeat disabled (missing REGISTRY_URL or AGENT_BASE_URL)")
            return

        url = registry_url.rstrip("/") + "/heartbeat"
        payload = {
            "name": agent_name,
            "version": agent_version,
            "base_url": agent_base_url,
            "meta": {
                "kind": "agent-http",
                "mode": "sync-only",
            },
        }

        log.info(f"heartbeat enabled registry={url} base_url={agent_base_url}")

        async with httpx.AsyncClient(timeout=3.0) as client:
            while not stop_event.is_set():
                try:
                    await client.post(url, json=payload)
                except Exception:
                    log.exception("heartbeat failed")
                await asyncio.sleep(heartbeat_interval_s)

    async def lifespan(app: FastAPI):
        nonlocal heartbeat_task
        heartbeat_task = asyncio.create_task(_heartbeat_loop())
        yield
        stop_event.set()
        if heartbeat_task:
            heartbeat_task.cancel()
            await asyncio.gather(heartbeat_task, return_exceptions=True)

    app = FastAPI(title=f"Agent: {sp.name}", version=sp.version, lifespan=lifespan)

    @app.get("/spec")
    def spec():
        return {
            "name": sp.name,
            "version": sp.version,
            "description": sp.description,
            "timeout_s": sp.timeout_s,
            "tags": sp.tags or [],
            "input_schema": sp.input_model.model_json_schema(),
            "output_schema": sp.output_model.model_json_schema(),
            "endpoints": {"invoke_sync": "/invoke"},
        }

    @app.get("/health")
    def health():
        return {"status": "UP", "agent": sp.name, "version": sp.version}

    @app.post("/invoke", response_model=AgentInvokeResponse)
    async def invoke(req: AgentInvokeRequest):
        verbose = bool(getattr(req.context, "verbose", False))

        try:
            inp = sp.input_model.model_validate(req.input)
            ctx = req.context

            # session-aware (optional)
            sess = await session_store.get(ctx.session_id)
            ctx.vars["session_state"] = sess

            out = await agent.run(inp, ctx)
            out_model = sp.output_model.model_validate(out)

            maybe_new = ctx.vars.get("session_state")
            if isinstance(maybe_new, dict):
                await session_store.set(ctx.session_id, maybe_new)

            meta = {"agent": sp.name, "version": sp.version, "mode": "sync"}
            if verbose and isinstance(ctx.vars.get("_debug"), dict):
                meta["debug"] = ctx.vars["_debug"]

            return AgentInvokeResponse(ok=True, output=out_model.model_dump(), meta=meta)

        except ValidationError as ve:
            details = {}
            if verbose:
                details["traceback"] = traceback.format_exc()

            return AgentInvokeResponse(
                ok=False,
                error=AgentError(code="VALIDATION_ERROR", message=str(ve), details=details),
                meta={"agent": sp.name, "version": sp.version, "mode": "sync"},
            )

        except Exception as e:
            # sempre loga stacktrace no servidor
            log.exception("agent runtime error")

            details = {}
            if verbose:
                details["traceback"] = traceback.format_exc()

            return AgentInvokeResponse(
                ok=False,
                error=AgentError(code="AGENT_RUNTIME_ERROR", message=repr(e), details=details),
                meta={"agent": sp.name, "version": sp.version, "mode": "sync"},
            )

    return app