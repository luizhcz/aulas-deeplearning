from __future__ import annotations
from pydantic import BaseModel
from typing import Any, Dict, Optional

class AppError(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = {}
    retryable: bool = False
    cause: Optional[str] = None