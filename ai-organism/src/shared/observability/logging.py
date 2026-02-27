from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

from shared.observability.context import (
    agent_name_var,
    request_id_var,
    session_id_var,
    tenant_id_var,
    trace_id_var,
    user_id_var,
)


def _is_debug_enabled() -> bool:
    v = os.getenv("DEBUG", "false").strip().lower()
    return v in {"1", "true", "yes", "y", "on"}


class JsonFormatter(logging.Formatter):
    """Structured logs as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        base: Dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        # Attach context (if present)
        ctx = {
            "request_id": request_id_var.get(),
            "trace_id": trace_id_var.get(),
            "session_id": session_id_var.get(),
            "tenant_id": tenant_id_var.get(),
            "user_id": user_id_var.get(),
            "agent": agent_name_var.get(),
        }
        ctx = {k: v for k, v in ctx.items() if v}
        if ctx:
            base.update(ctx)

        # Extras (safe)
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            base.update(extra)

        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(base, ensure_ascii=False)


_CONFIGURED = False


def configure_logging() -> None:
    """Configure root logger once.

    - JSON logs
    - DEBUG via env DEBUG=true
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    root.setLevel(logging.DEBUG if _is_debug_enabled() else logging.INFO)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def log_with_extra(logger: logging.Logger, level: int, msg: str, *, extra: Optional[Dict[str, Any]] = None):
    rec_extra = {"extra": extra or {}}
    logger.log(level, msg, extra=rec_extra)