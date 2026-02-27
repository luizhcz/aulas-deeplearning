from __future__ import annotations

"""Prometheus metrics helpers.

This project intentionally keeps the metrics surface small and stable.
"""

import time
from typing import Optional

from prometheus_client import Counter, Histogram


REQUESTS_TOTAL = Counter(
    "ai_org_requests_total",
    "Total HTTP requests",
    ["service", "route", "method", "status"],
)

REQUEST_LATENCY_SECONDS = Histogram(
    "ai_org_request_latency_seconds",
    "HTTP request latency in seconds",
    ["service", "route", "method"],
)

AGENT_INVOKE_TOTAL = Counter(
    "ai_org_agent_invoke_total",
    "Total agent invocations",
    ["agent", "version", "status", "error_code"],
)

AGENT_INVOKE_LATENCY_SECONDS = Histogram(
    "ai_org_agent_invoke_latency_seconds",
    "Agent invoke latency in seconds",
    ["agent", "version", "status"],
)

TOOL_CALLS_TOTAL = Counter(
    "ai_org_tool_calls_total",
    "Total tool calls",
    ["agent", "tool", "status"],
)


class Timer:
    def __init__(self):
        self._start = time.perf_counter()

    def stop(self) -> float:
        return max(0.0, time.perf_counter() - self._start)


def label_route(path: str) -> str:
    """Reduce cardinality: use raw path (no params) for this MVP."""
    return path