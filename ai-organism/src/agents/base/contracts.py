from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Type
from pydantic import BaseModel

@dataclass(frozen=True)
class AgentSpec:
    name: str
    version: str
    description: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    timeout_s: float = 6.0
    tags: List[str] | None = None

class BaseAgent(ABC):
    @classmethod
    @abstractmethod
    def spec(cls) -> AgentSpec: ...

    @abstractmethod
    async def run(self, inp: BaseModel, ctx: "AgentContext") -> BaseModel: ...