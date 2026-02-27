from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Optional, Type
from pydantic import BaseModel

from shared.contracts.http import AgentContext

@dataclass(frozen=True)
class AgentSpec:
    name: str
    version: str
    description: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    timeout_s: float = 10.0
    tags: Optional[List[str]] = None

class BaseAgent:
    def spec(self) -> AgentSpec:
        raise NotImplementedError

    async def run(self, inp: BaseModel, ctx: AgentContext) -> Any:
        raise NotImplementedError