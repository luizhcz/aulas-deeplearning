from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Optional

from shared.observability.logging import get_logger


def _debug_enabled() -> bool:
    v = os.getenv("DEBUG", "false").strip().lower()
    return v in {"1", "true", "yes", "y", "on"}


def _hash_payload(payload: Any) -> str:
    try:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    except Exception:
        raw = repr(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def audit_event(
    *,
    event: str,
    action: str,
    outcome: str,
    subject: Optional[Dict[str, Any]] = None,
    object_: Optional[Dict[str, Any]] = None,
    request: Optional[Dict[str, Any]] = None,
    response: Optional[Dict[str, Any]] = None,
    error: Optional[Dict[str, Any]] = None,
    sensitive_request: Optional[Any] = None,
    sensitive_response: Optional[Any] = None,
) -> None:
    """Emit an audit event.

    Sensitive payloads are only included when DEBUG=true.
    Otherwise we log only a hash to support forensic correlation.
    """
    lg = get_logger("audit")

    extra: Dict[str, Any] = {
        "audit": {
            "event": event,
            "action": action,
            "outcome": outcome,
            "subject": subject or {},
            "object": object_ or {},
            "request": request or {},
            "response": response or {},
            "error": error or {},
        }
    }

    if sensitive_request is not None:
        if _debug_enabled():
            extra["audit"]["sensitive_request"] = sensitive_request
        else:
            extra["audit"]["sensitive_request_hash"] = _hash_payload(sensitive_request)

    if sensitive_response is not None:
        if _debug_enabled():
            extra["audit"]["sensitive_response"] = sensitive_response
        else:
            extra["audit"]["sensitive_response_hash"] = _hash_payload(sensitive_response)

    lg.info("audit", extra={"extra": extra})