from __future__ import annotations

import time
import uuid
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from shared.observability.context import clear_context, set_context
from shared.observability.logging import get_logger
from shared.observability.metrics import REQUESTS_TOTAL, REQUEST_LATENCY_SECONDS, label_route


def _ensure_id(v: Optional[str]) -> str:
    if v and v.strip():
        return v.strip()
    return uuid.uuid4().hex


def instrument_fastapi(app: FastAPI, *, service_name: str) -> None:
    """Attach common middleware + /metrics endpoint."""
    lg = get_logger(f"obs.{service_name}")

    @app.middleware("http")
    async def _context_and_metrics_mw(request: Request, call_next: Callable):
        start = time.perf_counter()
        route = label_route(request.url.path)

        request_id = _ensure_id(request.headers.get("x-request-id"))
        trace_id = _ensure_id(request.headers.get("x-trace-id"))

        # Attach to context (available for all logs)
        set_context(request_id=request_id, trace_id=trace_id)

        try:
            response: Response = await call_next(request)
        except Exception:
            lg.exception("unhandled exception")
            raise
        finally:
            elapsed = max(0.0, time.perf_counter() - start)
            status = "500"
            try:
                status = str(getattr(locals().get("response"), "status_code", 500))
            except Exception:
                pass

            REQUESTS_TOTAL.labels(service=service_name, route=route, method=request.method, status=status).inc()
            REQUEST_LATENCY_SECONDS.labels(service=service_name, route=route, method=request.method).observe(elapsed)

            # propagate ids back
            try:
                if locals().get("response") is not None:
                    response.headers["x-request-id"] = request_id
                    response.headers["x-trace-id"] = trace_id
            except Exception:
                pass

            clear_context()

        return response

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)